from flask import Blueprint, jsonify, request
from app.service.hello_service import get_hello_message
from app.models.registration_model import AddUserSchema, AddFieldSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import USER_HANDLER,FIELD_HANDLER

reg_blueprint = Blueprint('registration', __name__)

@reg_blueprint.route('/add-user', methods=['POST'])
def add_registration():
    """
    Sample user JSON:
    {
        "user_id": "user_001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "whatsapp_number": "+1234567890",
        "location": {
            "latitude": 12.345678,
            "longitude": 98.765432
        }
    }
    """
    data = request.get_json()
    try:
        validated = AddUserSchema(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.errors()}), 400

    user_id = validated.user_id
    name = validated.name
    email = validated.email
    whatsapp_number = validated.whatsapp_number
    location = validated.location

    try:
        USER_HANDLER.add_user({
            'user_id': user_id,
            'name': name,
            'email': email,
            'whatsapp_number': whatsapp_number,
            'location': {
                'latitude': location.latitude,
                'longitude': location.longitude
            },
            'field_ids': []  # Assuming field_ids is an empty list for new users
        })
        return jsonify({'success': True, 'message': 'Registration successful'}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@reg_blueprint.route('/get-user-deatils', methods=['POST'])
def get_user_details():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    try:
        user_details = USER_HANDLER.get_by_id(
            unique_field='user_id',
            value=user_id
        )
        # Convert _id to string if necessary
        if isinstance(user_details, dict) and '_id' in user_details:
            user_details['_id'] = str(user_details['_id'])

        if user_details:
            return jsonify({'success': True, 'data': user_details}), 200
        else:
            return jsonify({'success': False, 'message': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@reg_blueprint.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400
    
    try:
        USER_HANDLER.delete_by_id(
            unique_field='user_id',
            value=user_id
        )
        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500





