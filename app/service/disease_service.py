from app.mongo.agri_handlers import ALERT_STORAGE_HANDLER,FIELD_HANDLER
from app.llms.openai import LangchainOpenaiJsonEngine
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from app.llms.gemini import GeminiImageUnderstandingEngine


class AgriDiseaseAction(BaseModel):
    """
    Represents an action to be taken based on agricultural insights.
    """
    is_disease: bool = Field(
        ...,
        description="Indicates whether any disease is detected in the image."
    )
    action_body: str = Field(
        ...,
        description="Description of the action to be taken and why it is necessary."
    )
    action_severity: str = Field(
        ...,
        description="Severity of the action, e.g., 'low', 'medium', 'high', 'critical'."
    )

class DiseasePredictionPipeline:
    """
    Pipeline for predicting agricultural diseases from images.
    """
    def __init__(self):
        self.img_engine = GeminiImageUnderstandingEngine()
        self.action_engine = LangchainOpenaiJsonEngine(
            model_name="gpt-4o-mini",
            temperature=0.2,
            sampleBaseModel=AgriDiseaseAction,
            systemPromptText= """You are an expert in agricultural disease detection and management.
You will given with analysis of an agricultural image about any disease or infection of plants.
Your task is to determine if there is a disease is present in the analysis and if so, provide a detailed action plan to address it which can be immediately implemented.
If there is no disease then return is_disease as False and action_body as "No disease detected in the image." and action_severity as "low".
""")
        
    def run(self, image_path: str, sensor_hub_id: str) -> Dict[str, Any]:
        """
        Run the disease prediction pipeline on the given image.
        
        :param image_path: Path to the image file.
        :return: Dictionary containing the prediction results.
        """
        try:
            # Step 1: Extract crop type from the FIELD_HANDLER
            field_details = FIELD_HANDLER.get_fields_by_hub_id(sensor_hub_id)
            if not field_details:
                return {"error": "No field found for the given Sensor Hub ID"}
            crop_type = field_details[0]['crop_type']

            # Step 1: Analyze the image using Gemini
            gemini_response = self.img_engine.run(image_path, f"This is a image of {crop_type} plant. Analyze this agricultural image for any diseases or infections. If there is a disease tell what kind of disease and what is the severity of the disease. Don't use markdown. Write in single paragraph.")
            if "error" in gemini_response:
                return {"error": gemini_response["error"]}
            
            # print("Gemini Response:", gemini_response["result"])
            
            # Step 2: Process the response and generate action
            action_response = self.action_engine.run(
                "Analysis of the agricultural image: " + gemini_response["result"]
            )[0]
            if action_response['is_disease']:
                timstamp = datetime.now().isoformat()
                payload = {
                    "timestamp": timstamp,
                    "alert_id": f"alert_disease_0_{timstamp}",
                    "type": "disease",
                    "action_body": action_response['action_body'],
                    "action_severity": action_response['action_severity'],
                    "sensor_hub_id": sensor_hub_id
                }
                ALERT_STORAGE_HANDLER.add_alert(payload)
                return payload
            else:
                return {"result": "No disease detected."}

        except Exception as e:
            return {"error": str(e)}
        


DISEASE_PREDICTION_PIPELINE = DiseasePredictionPipeline()