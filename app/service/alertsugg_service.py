from app.llms.openai import LangchainOpenaiJsonEngine
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta

from app.service.agrireq_service import AGRICULTURAL_INFO_GENERATOR
from app.service.sensor_analysis import SENSOR_SQL_LLM_ENGINE
from app.service.weather_service import TOMORROW_WEATHER_SERVICE
from app.mongo.agri_handlers import ALERT_STORAGE_HANDLER
load_dotenv()


class AgriAction(BaseModel):
    """
    Represents an action to be taken based on agricultural insights.
    """
    action_body: str = Field(
        ...,
        description="Description of the action to be taken."
    )
    action_severity: str = Field(
        ...,
        description="Severity of the action, e.g., 'low', 'medium', 'high', 'critical'."
    )

class AgriActions(BaseModel):
    """
    Represents a collection of actions to be taken based on agricultural insights.
    """
    actions: List[AgriAction] = Field(
        ...,
        description="List of actions to be taken."
    )








class AgricultureActionSuggestor:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.engine = LangchainOpenaiJsonEngine(
            model_name=model_name,
            temperature=temperature,
            sampleBaseModel=AgriActions,
            systemPromptText="""You are an expert in agriculture and farming practices.
Your task is to suggest actions based on agricultural insights.
You will receive three types of information: crop-ideal situation, sensor alerts, and weather buckets.
- crop-ideal situation: The ideal conditions for the crop, including nutrient requirements, soil type, irrigation needs, pest management, and suitable weather conditions.
- sensor alerts: The current conditions received from on-site sensors, including humidity , nutrient levels, and other relevant metrics.
- weather buckets: The previous-current-future weather conditions, including temperature, rainfall, and other relevant metrics.

Your task is to analyze these inputs and suggest actions that can be taken by the farmer to optimize agricultural practices.
Instructions:
- Ensure that the actions are practical, actionable, and relevant to the current agricultural context.
- State the each action with relevant metric and unit of measurement where applicable.
- Only suggest actions which are highlighted in the sensor alerts and weather buckets. Don't suggest all ideal actions.
- Only suggest actions that can be taken immediately or in the near future based on the current conditions.
- Return an empty list if no actions are suggested.
"""
        )

    def suggest_actions(self, crop_ideal: Dict[str, Any], sensor_alerts: List[str], weather_buckets: Dict[str, str]) -> Dict[str, List[AgriAction]]:
        # Generate actions using the engine
        crop_ideal_text = '\n- '.join([f"{key}: {value}" for key, value in crop_ideal.items()])
        sensor_alerts_text = '\n- '.join(sensor_alerts)
        
        header_prompt = f"""User: What actions can be taken based on the following agricultural insights?
    Crop Ideal Situation: {crop_ideal_text}
    Sensor Alerts: {sensor_alerts_text}"""
        
        actions = {}
        timestamp = datetime.now().isoformat()
        for w_key, w_value in weather_buckets.items():
            prompt = f"{header_prompt}\n{w_value}\n\nNow suggest actions based on the above information."
            result = self.engine.run(prompt)[0]
            actions[w_key] = result.get('actions', []) 
            # convert to list of dict
            actions[w_key] = [{
                **x.dict(),
                'timestamp': timestamp,
                'alert_id': f"alert_{w_key}_{i}_{timestamp.replace(':', '-')}",
                "type": w_key
                } for i, x in enumerate(actions[w_key])] if isinstance(actions[w_key], list) else []
        actions['sensor_alerts'] = [{
            'timestamp': timestamp,
            'alert_id': f"alert_sensor_{i}_{timestamp.replace(':', '-')}",
            'action_body': x, 
            'type': 'sensor',
            'action_severity': 'high' # Assuming a default severity, can be adjusted based on context
        } for i, x in enumerate(sensor_alerts)] if isinstance(sensor_alerts, list) else []
        return actions



AGRICULTURE_ACTION_SUGGESTOR = AgricultureActionSuggestor()

def run_action_suggestion_pipeline(
    latitude: float,
    longitude: float,
    days: int,
    crop_type: str,
    sensor_hub_id: str
) -> Dict[str, List]:
    """
    Run the action suggestion pipeline with the provided inputs.
    
    :param crop_ideal: Ideal conditions for the crop.
    :param sensor_alerts: Current conditions received from on-site sensors.
    :param weather_buckets: Previous-current-future weather conditions.
    :return: Suggested actions based on the inputs.
    """
    ideal_agri_result = AGRICULTURAL_INFO_GENERATOR.generate_requirements(
        lat=latitude,
        lon=longitude,
        crop_type=crop_type
    )

    sensor_alerts = SENSOR_SQL_LLM_ENGINE.run_pipeline(
        task_description="Analyze the sensor data and generate detailed insights about different sensor metrics. Also their interpretation among the lines of agriculture.",
        sensor_hub_id=sensor_hub_id
    ).get('insights', [])
    

    weather_buckets = TOMORROW_WEATHER_SERVICE(
        latitude=latitude,
        longitude=longitude,
        days=days
    )

    actions = AGRICULTURE_ACTION_SUGGESTOR.suggest_actions(
        crop_ideal=ideal_agri_result,
        sensor_alerts=sensor_alerts,
        weather_buckets=weather_buckets
    )

    for action_bucket, action_list in actions.items():
        for action in action_list:
            ALERT_STORAGE_HANDLER.add_alert({
                **action,
                'sensor_hub_id': sensor_hub_id
            })

    return actions
