from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from app.models.registration_model import AddUserSchema, AddFieldSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import USER_HANDLER, FIELD_HANDLER

fin_blueprint = Blueprint('fin', __name__)

@fin_blueprint.route('/', methods=['GET', 'POST'])
def hello():
    return jsonify({'message': "Not Implemented"}), 501
