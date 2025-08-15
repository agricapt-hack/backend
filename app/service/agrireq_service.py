from app.llms.openai import LangchainOpenaiJsonEngine
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
load_dotenv() 






class AgricultureRequirements(BaseModel):
    """
    Model to represent the requirements for agriculture information. 
    """
    nuturient_requirements: str = Field(
        ...,
        description="Nutrient requirements for the crop, including NPK and micronutrients."
    )
    soil_type: str = Field(
        ...,
        description="Soil type suitable for the crop, including pH and texture."
    )
    irrigation_requirements: str = Field(
        ...,
        description="Irrigation requirements for the crop, including frequency and method."
    )
    pest_management: str = Field(
        ...,
        description="Pest management strategies for the crop, including organic and chemical options."
    )
    weather_conditions: str = Field(
        ...,
        description="Weather conditions suitable for the crop, including temperature and rainfall."
    )







class AgricultureInfoGenerator:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        self.engine = LangchainOpenaiJsonEngine(
            model_name=model_name,
            temperature=temperature,
            sampleBaseModel=AgricultureRequirements,
            systemPromptText="""You are an expert in agriculture and farming practices. 
Your task is to provide detailed and accurate information about the requirements from user given location and crop type.
You will receive a location and crop type, and you need to generate comprehensive agricultural requirements.
The information should be comprehensive, covering nutrient requirements, soil type, irrigation needs, pest management, and suitable weather conditions.
Ensure that the information is practical and applicable to the specified location and crop type.
State the each requirement with relevant metric and unit of measurement where applicable.
"""
        )
        self.geolocator = Nominatim(user_agent="HarvestAI")

    def generate_requirements(self, lat:float, lon:float, crop_type:str) -> Dict[str, Any]:
        lat_lon = f"{lat}, {lon}"
        address = self.geolocator.reverse(lat_lon)
        # From current date , retrieve the month
        current_date = datetime.now()
        month = current_date.strftime("%B")

        # Generate agricultural requirements using the engine
        prompt = f"User: Generate agricultural requirements for {crop_type} at {address} in {month}."
        print(f"Prompt: {prompt}")
        result = self.engine.run(prompt)[0]
        return result
    



AGRICULTURAL_INFO_GENERATOR = AgricultureInfoGenerator()