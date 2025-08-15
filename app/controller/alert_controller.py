from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from app.models.registration_model import AddUserSchema, AddFieldSchema
from pydantic import ValidationError
from app.mongo.agri_handlers import FIELD_HANDLER, ALERT_STORAGE_HANDLER, AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER
from app.service.alertsugg_service import run_action_suggestion_pipeline

alert_blueprint = Blueprint('alert', __name__)


@alert_blueprint.route('/trigger-alert', methods=['POST'])
def trigger_alert():
    hub_id = request.json.get('sensor_hub_id')
    if not hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400

    try:
        field_details = FIELD_HANDLER.get_fields_by_hub_id(hub_id)
        if not field_details:
            return jsonify({'success': False, 'message': 'No field found for the given Sensor Hub ID'}), 404
        print(f"Field details for hub_id {hub_id}: {field_details}")
        latitude = field_details[0]['field_location']['latitude']
        longitude = field_details[0]['field_location']['longitude']
        crop_type = field_details[0]['crop_type']
        days = 7
        print(f"Triggering action suggestions for hub_id: {hub_id}, latitude: {latitude}, longitude: {longitude}, crop_type: {crop_type}, days: {days}")
        action_suggestions = run_action_suggestion_pipeline(latitude, longitude, days=days, crop_type=crop_type, sensor_hub_id=hub_id)
        return jsonify({'success': True, 'action_suggestions': action_suggestions}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@alert_blueprint.route('/get-alerts-by-hub', methods=['POST'])
def get_alerts():
    """
    Sample request JSON:
    {
        "sensor_hub_id": "hub_1"
    }
    """
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')

    if not sensor_hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400

    try:
        alerts = ALERT_STORAGE_HANDLER.get_alerts_by_hub_id(sensor_hub_id)
        if not alerts:
            return jsonify({'success': False, 'message': 'No alerts found for the given Sensor Hub ID'}), 404
        # Convert _id to string if necessary
        for alert in alerts:
            if isinstance(alert, dict) and '_id' in alert:
                alert['_id'] = str(alert['_id'])
                del alert['vector']  # Assuming vector is not needed in the response
        return jsonify({'success': True, 'alerts': alerts}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@alert_blueprint.route('/get-alerts-by-user', methods=['POST'])
def get_alerts_by_user():
    """
    Sample request JSON:
    {
        "user_id": "user_1"
    }
    """
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'}), 400

    try:
        all_fields = FIELD_HANDLER.get_fields_by_user_id(user_id)
        hub_ids = [field['sensor_hub_id'] for field in all_fields]
        if not hub_ids:
            return jsonify({'success': False, 'message': 'No fields found for the given User ID'}), 404

        alerts = ALERT_STORAGE_HANDLER.get_alerts_by_hub_ids(hub_ids)
        if not alerts:
            return jsonify({'success': False, 'message': 'No alerts found for the given User ID'}), 404
        # Convert _id to string if necessary
        for alert in alerts:
            if isinstance(alert, dict) and '_id' in alert:
                alert['_id'] = str(alert['_id'])
                del alert['vector']
        return jsonify({'success': True, 'alerts': alerts}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@alert_blueprint.route('/trigger-product-service', methods=['POST'])
def trigger_product_service():
    """
    Sample request JSON:
    {
        "sensor_hub_id": "hub_1",
        "date": "2023-10-01"
    }
    """
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')
    date = data.get('date')

    if not sensor_hub_id or not date:
        return jsonify({'success': False, 'message': 'Sensor Hub ID and date are required'}), 400

    try:
        # Assuming a function to trigger product service based on sensor hub ID and date
        result = ALERT_STORAGE_HANDLER.suggest_for_date(
            sensor_hub_id=sensor_hub_id,
            date=date
        )

        if not result:
            return jsonify({'success': False, 'message': 'No product service suggestions found for the given Sensor Hub ID and date'}), 404
        # Convert _id to string if necessary
        for p in result['products']:
            p = p['product_service']
            if isinstance(p, dict) and '_id' in p:
                p['_id'] = str(p['_id'])
                del p['vector']
        for s in result['services']:
            s = s['product_service']
            if isinstance(s, dict) and '_id' in s:
                s['_id'] = str(s['_id'])
                del s['vector']
        return jsonify({'success': True, 'result': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@alert_blueprint.route('/delete-alert', methods=['POST'])
def delete_alert():
    """
    Sample request JSON:
    {
        "alert_id": "alert_001"
    }
    """
    data = request.get_json()
    alert_id = data.get('alert_id')

    if not alert_id:
        return jsonify({'success': False, 'message': 'Alert ID is required'}), 400

    try:
        result = ALERT_STORAGE_HANDLER.delete_by_id(
            unique_field='alert_id',
            value=alert_id
        )
        if result == 0:
            return jsonify({'success': False, 'message': 'Alert not found'}), 404

        return jsonify({'success': True, 'message': 'Alert deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    

@alert_blueprint.route('/delete-suggestion', methods=['POST'])
def delete_suggestion():
    """
    Sample request JSON:
    {
        "suggestion_id": "suggestion_001"
    }
    """
    data = request.get_json()
    suggestion_id = data.get('suggestion_id')

    if not suggestion_id:
        return jsonify({'success': False, 'message': 'Suggestion ID is required'}), 400

    try:
        result = AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.delete_by_id(
            unique_field='suggestion_id',
            value=suggestion_id
        )
        if result == 0:
            return jsonify({'success': False, 'message': 'Suggestion not found'}), 404

        return jsonify({'success': True, 'message': 'Suggestion deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@alert_blueprint.route('/delete-alerts-by-hubid', methods=['POST'])
def delete_alerts_by_hubid():
    """
    Sample request JSON:
    {
        "sensor_hub_id": "hub_1"
    }
    """
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')

    if not sensor_hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400

    try:
        result = ALERT_STORAGE_HANDLER.delete_by_query(
            query={'sensor_hub_id': sensor_hub_id}
        )
        if result == 0:
            return jsonify({'success': False, 'message': 'No alerts found for the given Sensor Hub ID'}), 404

        return jsonify({'success': True, 'message': 'Alerts deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@alert_blueprint.route('/delete-suggestion-by-hubid', methods=['POST'])
def delete_suggestion_by_hubid():
    """
    Sample request JSON:
    {
        "sensor_hub_id": "hub_1"
    }
    """
    data = request.get_json()
    sensor_hub_id = data.get('sensor_hub_id')

    if not sensor_hub_id:
        return jsonify({'success': False, 'message': 'Sensor Hub ID is required'}), 400

    try:
        result = AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.delete_by_query(
            query={'sensor_hub_id': sensor_hub_id}
        )
        if result == 0:
            return jsonify({'success': False, 'message': 'No suggestions found for the given Sensor Hub ID'}), 404

        return jsonify({'success': True, 'message': 'Suggestions deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500