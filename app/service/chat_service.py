from app.llms.openai import LangchainOpenaiSimpleChatEngine, LangchainOpenaiJsonEngine
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime


GENERAL_CHAT_ENGINE = LangchainOpenaiSimpleChatEngine(
    model_name="gpt-4o-mini",
    temperature=0.2,
    systemPromptText="""You are a helpful agricultural and financial assistant.
You will be given user queries related to agriculture or financial topics.
If user asks about agriculture, provide insights on crops, diseases, and farming practices.
If user asks about financial topics, provide insights on financial products, services, and advice.
If user asks about any other topic apart from agriculture and finance, tell them to ask about agriculture or financial topics only.
""")


def general_chat_service(query) -> Dict[str, Any]:
    """
    General chat service for handling user queries and providing responses.
    """
    result = GENERAL_CHAT_ENGINE.run(query)
    return {
        "response": result
    }