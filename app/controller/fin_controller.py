from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from app.models.registration_model import AddUserSchema, AddFieldSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import USER_HANDLER, FIELD_HANDLER
from app.service.yt_service import YTSERVICE_HANDLER

fin_blueprint = Blueprint('fin', __name__)

@fin_blueprint.route('/', methods=['GET', 'POST'])
def hello():
    return jsonify({'message': "Not Implemented"}), 501


@fin_blueprint.route('/yt-search', methods=['POST'])
def yt_search():
    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        results = YTSERVICE_HANDLER.search(query)
        return jsonify({"videos": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
