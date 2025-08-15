from flask import Blueprint, jsonify, request
from app.service.hello_service import get_hello_message
from app.mongo.agri_handlers import reset_handlers

hello_blueprint = Blueprint('hello', __name__)

@hello_blueprint.route('/hello', methods=['GET'])
def hello():
    return jsonify(get_hello_message()), 200

@hello_blueprint.route('/reset-handlers', methods=['POST'])
def reset():
    """
    Reset the application state.
    """
    try:
        reset_handlers()
        return jsonify({'success': True, 'message': 'Application state reset successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500