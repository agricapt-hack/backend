from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from app.models.registration_model import AddUserSchema, AddFieldSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import USER_HANDLER, FIELD_HANDLER
from app.service.weather_service import TOMORROW_WEATHER_SERVICE
from app.postgres.rds import RDS_POSTGRES_DB

field_blueprint = Blueprint('field', __name__)


@field_blueprint.route('/add-field', methods=['POST'])
def add_field():
    """
    Sample field JSON:
    {
        "field_id": "field_001",
        "user_id": "user_001",
        "field_name": "North Farm",
        "field_location": {
            "latitude": 12.345678,
            "longitude": 98.765432
        },
        "sensor_hub_id": "hub_1",
        "crop_type": "rice",
        "user_texts": ["good soil", "needs irrigation"]
    }
    """
    data = request.get_json()
    try:
        validated = AddFieldSchema(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.errors()}), 400

    field_id = validated.field_id
    user_id = validated.user_id
    field_name = validated.field_name
    field_location = validated.field_location
    sensor_hub_id = validated.sensor_hub_id
    crop_type = validated.crop_type
    user_texts = validated.user_texts

    # Check if the user exists or field_id is already taken
    if not USER_HANDLER.get_by_id(unique_field='user_id', value=user_id):
        return jsonify({'success': False, 'message': 'User does not exist'}), 404

    if FIELD_HANDLER.get_by_id(unique_field='field_id', value=field_id):
        return jsonify({'success': False, 'message': 'Field ID is already taken'}), 409

    try:
        FIELD_HANDLER.add_field({
            'field_id': field_id,
            'user_id': user_id,
            'field_name': field_name,
            'field_location': {
                'latitude': field_location.latitude,
                'longitude': field_location.longitude
            },
            'sensor_hub_id': sensor_hub_id,
            'crop_type': crop_type,
            'user_texts': user_texts
        })
        return jsonify({'success': True, 'message': 'Field added successfully'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    


@field_blueprint.route('/get-all-fields-by-userid', methods=['POST'])
def get_all_fields_by_userid():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    try:
        fields = FIELD_HANDLER.get_fields_by_user_id(
            user_id=user_id
        )
        if not fields:
            return jsonify({'success': False, 'message': 'No fields found for this user'}), 404
        # Convert _id to string if necessary
        for field in fields:
            if isinstance(field, dict) and '_id' in field:
                field['_id'] = str(field['_id'])
        return jsonify({'success': True, 'fields': fields}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@field_blueprint.route('/get-field-by-fieldid', methods=['POST'])
def get_field_by_id():
    data = request.get_json()
    field_id = data.get('field_id')
    
    if not field_id:
        return jsonify({'success': False, 'message': 'Field ID is required'}), 400
    
    try:
        field = FIELD_HANDLER.get_by_id(
            unique_field='field_id',
            value=field_id
        )
        if field:
            # Convert _id to string if necessary
            if isinstance(field, dict) and '_id' in field:
                field['_id'] = str(field['_id'])
            return jsonify({'success': True, 'field': field}), 200
        else:
            return jsonify({'success': False, 'message': 'Field not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@field_blueprint.route('/delete-field', methods=['POST'])
def delete_field():
    data = request.get_json()
    field_id = data.get('field_id')
    
    if not field_id:
        return jsonify({'success': False, 'message': 'Field ID is required'}), 400
    
    try:
        FIELD_HANDLER.delete_by_id(
            unique_field='field_id',
            value=field_id
        )
        return jsonify({'success': True, 'message': 'Field deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@field_blueprint.route('/get-sensor-data-by-hubid', methods=['POST'])
def get_sensor_data_by_hub():   
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')
    
    if not sensor_hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400
    
    try:
        sensor_data = RDS_POSTGRES_DB.query_data(
            f"SELECT * FROM arduino_data WHERE sensor_hub_id = '{sensor_hub_id}'"
        )
        if sensor_data:
            return jsonify({'success': True, 'data': sensor_data}), 200
        else:
            return jsonify({'success': False, 'message': 'No data found for this hub'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@field_blueprint.route('/get-weather-data-by-hubid', methods=['POST'])
def get_weather_data_by_hub():
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')
    
    if not sensor_hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400
    
    try:
        field_details = FIELD_HANDLER.get_fields_by_hub_id(sensor_hub_id)
        if not field_details:
            return jsonify({'success': False, 'message': 'No field found for the given Sensor Hub ID'}), 404
        latitude = field_details[0]['field_location']['latitude']
        longitude = field_details[0]['field_location']['longitude']
        weather_data = TOMORROW_WEATHER_SERVICE(latitude, longitude, days=7, formated=False)
        return jsonify({'success': True, 'weather_data': weather_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500