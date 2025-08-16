from flask import Blueprint, request, jsonify
from app.service.hello_service import get_hello_message
from pydantic import ValidationError
from app.service.notification_service import EMAIL_NOTIFICATION_SERVICE

notification_blueprint = Blueprint('notification', __name__)


@notification_blueprint.route('/trigger-email-notifications', methods=['POST'])
def trigger_email_notifications():
    """
    Trigger email notifications for alerts and suggestions.
    Sample request JSON:
    {
        "date": "2025-08-16"
    }
    """
    data = request.get_json()
    date = data.get('date')

    if not date:
        return jsonify({'success': False, 'message': 'Date is required'}), 400

    try:
        EMAIL_NOTIFICATION_SERVICE.trigger_email_notifications(date)
        return jsonify({'success': True, 'message': 'Email notifications triggered successfully'}), 200
    except ValidationError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

