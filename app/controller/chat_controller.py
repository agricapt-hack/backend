from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from app.mongo.agri_handlers import FIELD_HANDLER, ALERT_STORAGE_HANDLER, AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER
from app.service.chat_service import general_chat_service
import os

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/general-chat', methods=['POST'])
def general_chat():
    """
    Endpoint for general chat service.
    Expects JSON with a 'query' field.
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Invalid input, expected JSON with a "query" field'}), 400

    query = data['query']
    
    try:
        result = general_chat_service(query)
        return jsonify(result), 200
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@chat_blueprint.route('/field-chat', methods=['POST'])
def field_chat():
    """
    Endpoint for field chat service.
    Expects JSON with a 'query' and 'sensor_hub_id' field.
    """
    data = request.get_json()
    if not data or 'query' not in data or 'sensor_hub_id' not in data:
        return jsonify({'error': 'Invalid input, expected JSON with a "query" and "sensor_hub_id" field'}), 400

    query = data['query']
    sensor_hub_id = data['sensor_hub_id']

    try:
        result = general_chat_service(query)
        return jsonify(result), 200
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500