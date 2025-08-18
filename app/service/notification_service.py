import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import requests
import os
from app.mongo.agri_handlers import ALERT_STORAGE_HANDLER,AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER, FIELD_HANDLER


class EmailNotificationService:
    def __init__(self):
        self.sender_email = os.getenv("SENDER_MAIL")
        self.sender_password = os.getenv("SENDER_PASSWORD")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.whatsapp_server_url = "https://harvestai-backend.onrender.com/send" # Need to post to this URL with {"to": <whatsapp_number>, "message": <message>}

    def get_recipient_email_and_body_for_alerts(self, date):
        """
        Search in ALERT_STORAGE_HANDLER for the given date alerts with delivery_status not having 'email' in it. Fetch the alert_id, sensor_hub_id, action_body, type, action_severity
        Then fetch the email from FIELD_HANDLER using sensor_hub_id.
        Create a Subject and Body for the email.
        return the a list of {
            "alert_id": alert_id,
            "email": email,
            "subject": subject,
            "body": body,
            "delivery_status": 
        } for each alert found.

        Add appropriate emojis to the subject and body based on the alert type and severity. 
        Severity can be 'low', 'medium', 'high', 'critical'. Emojis can be:
        - low: 🌱
        - medium: 🚨
        - high: 🔴
        - critical: ⚠️

        Type can be 'rain', 'temperature', 'misc' or 'sensor'
        Emojis can be:
        - rain: 🌧
        - temperature: 🌡
        - misc: ❓
        - sensor: 🛠
        - disease: 🦠
        """
        alerts = ALERT_STORAGE_HANDLER.get_by_query(
            query={
                "timestamp": {"$regex": f"^{date}"}
            }
        )
        print(len(alerts), "alerts found for date:", date)
        recipient_info = []

        for alert in alerts:
            if 'email' not in alert.get('delivery_status', ''):
                sensor_hub_id = alert.get('sensor_hub_id')
                cur_delivery_status = alert.get('delivery_status', '')
                user = FIELD_HANDLER.get_user_by_hub_id(sensor_hub_id)
                email = user.get('email') if user else None
                whatsapp_number = "+918388063520" #user.get('whatsapp_number') if user else None
                name = user.get('name') if user else "User"
                if email:
                    emoji_severity = {
                        'low': '🌱',
                        'medium': '🚨',
                        'high': '🔴',
                        'critical': '⚠️'
                    }.get(alert['action_severity'], '')
                    emoji_type = {
                        'rain': '🌧',
                        'temperature': '🌡',
                        'misc': '❓',
                        'sensor': '🛠',
                        'disease': '🦠'
                    }.get(alert['type'], '')
                    subject = f"[HARVEST.AI ALERT] Alert Notification for {emoji_type} on {date} {emoji_severity}"
                    body = f"Hi {name},\nAlert ID: {alert['alert_id']}\nSensor Hub ID: {sensor_hub_id}\nAction Body: {alert['action_body']}\nType: {alert['type']}\nSeverity: {alert['action_severity']}"
                    recipient_info.append({
                        "alert_id": alert['alert_id'],
                        "email": email,
                        "whatsapp_number": whatsapp_number,
                        "subject": subject,
                        "body": body,
                        "delivery_status": cur_delivery_status
                    })

        return recipient_info
    
    def get_recipient_email_and_body_for_suggestions(self, date):
        """
        Fetch suggestions for the given date from AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.
        Return a list of {
            "email": email,
            "subject": subject,
            "body": body,
            "suggestion_id": suggestion_id,
            "delivery_status": cur_delivery_status
        } for each suggestion found.
        Emoji at the subject is :  🌱
        emoji at body for products is:  🛒
        emoji at body for services is:  🔧
        """
        suggestions = AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.get_by_query(
            query={
                "timestamp": {"$regex": f"^{date}"}
            }
        )
        recipient_info = []
        print(len(suggestions), "suggestions found for date:", date)

        for suggestion in suggestions:
            if 'email' in suggestion.get('delivery_status', ''):
                continue
            sensor_hub_id = suggestion.get('sensor_hub_id')
            cur_delivery_status = suggestion.get('delivery_status', '')
            user = FIELD_HANDLER.get_user_by_hub_id(sensor_hub_id)
            email = user.get('email') if user else None
            whatsapp_number = "+918388063520" #user.get('whatsapp_number') if user else None
            name = user.get('name') if user else "User"
            if email:
                subject = f"[HARVEST.AI SUGGESTION] Suggestions for {date} 🌱"
                body = f"Hi {name},\nSuggestion ID: {suggestion['suggestion_id']}\nSensor Hub ID: {sensor_hub_id}"
                if "products" in suggestion['suggestions']:
                    body += f"\n 🛒: {suggestion['suggestions']['products']}"
                if "services" in suggestion['suggestions']:
                    body += f"\n🔧 {suggestion['suggestions']['services']}"
                recipient_info.append({
                    "email": email,
                    "whatsapp_number": whatsapp_number,
                    "subject": subject,
                    "body": body,
                    "suggestion_id": suggestion['suggestion_id'],
                    "delivery_status": cur_delivery_status
                })

        return recipient_info
    

    def process_whatsapp_notifications(self, recipient_info):
        # Step 1: Group alerts by whatsapp_number and concat body 
        # Step 2: Group suggestions by whatsapp_number and concat body 
        whatsapp_alert_notifications = {}
        whatsapp_suggestion_notifications = {}
        for info in recipient_info:
            if 'whatsapp_number' in info and info['whatsapp_number']:
                whatsapp_number = info['whatsapp_number']
                if 'alert_id' in info:
                    if whatsapp_number not in whatsapp_alert_notifications:
                        whatsapp_alert_notifications[whatsapp_number] = {
                            "body": "",
                            "alerts": []
                        }
                    whatsapp_alert_notifications[whatsapp_number]['body'] += f"\n{info['body']}"
                    whatsapp_alert_notifications[whatsapp_number]['alerts'].append(info['alert_id'])
                elif 'suggestion_id' in info:
                    if whatsapp_number not in whatsapp_suggestion_notifications:
                        whatsapp_suggestion_notifications[whatsapp_number] = {
                            "body": "",
                            "suggestions": []
                        }
                    whatsapp_suggestion_notifications[whatsapp_number]['body'] += f"\n{info['body']}"
                    whatsapp_suggestion_notifications[whatsapp_number]['suggestions'].append(info['suggestion_id'])

        # Step 3: Send notifications via WhatsApp
        for whatsapp_number, alert_info in whatsapp_alert_notifications.items():
            if whatsapp_number!="+918388063520":
                continue
            message = f"Hi, you have the following alerts:\n{alert_info['body']}\nAlerts: {', '.join(alert_info['alerts'])}"
            payload = {"to": whatsapp_number, "message": message}
            try:
                response = requests.post(self.whatsapp_server_url, json=payload)
                response.raise_for_status()
                print(f"WhatsApp alert sent to {whatsapp_number}")
            except requests.RequestException as e:
                print(f"Failed to send WhatsApp alert to {whatsapp_number}: {e}")

        # Step 4: Send suggestions via WhatsApp
        for whatsapp_number, suggestion_info in whatsapp_suggestion_notifications.items():
            message = f"Hi, you have the following suggestions:\n{suggestion_info['body']}\nSuggestions: {', '.join(suggestion_info['suggestions'])}"
            payload = {"to": whatsapp_number, "message": message}
            try:
                response = requests.post(self.whatsapp_server_url, json=payload)
                response.raise_for_status()
                print(f"WhatsApp suggestion sent to {whatsapp_number}")
            except requests.RequestException as e:
                print(f"Failed to send WhatsApp suggestion to {whatsapp_number}: {e}")



    def trigger_email_notifications(self, date):
        """
        Trigger email notifications for alerts and suggestions for the given date.
        """
        alert_recipients = self.get_recipient_email_and_body_for_alerts(date)
        suggestion_recipients = self.get_recipient_email_and_body_for_suggestions(date)

        all_recipients = alert_recipients + suggestion_recipients

        if not all_recipients:
            print("No recipients found for date:", date)
            return
        
        # Send whatsapp notifications
        self.process_whatsapp_notifications(all_recipients)


        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)

            for recipient in all_recipients:
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = recipient['email']
                msg['Subject'] = recipient['subject']
                msg.attach(MIMEText(recipient['body'], 'plain'))

                server.send_message(msg)
                print(f"Email sent to {recipient['email']} with subject: {recipient['subject']}")

            # # Update delivery status in ALERT_STORAGE_HANDLER and AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER
            # for alert in alert_recipients:
            #     ALERT_STORAGE_HANDLER.update_delivery_status(
            #         alert_id=alert['alert_id'],
            #         delivery_status=alert['delivery_status']+"+email+wap"
            #     )
            # for suggestion in suggestion_recipients:
            #     AGRI_PRODUCT_SERVICE_SUGGESTION_HANDLER.update_delivery_status(
            #         suggestion_id=suggestion['suggestion_id'],
            #         delivery_status=suggestion['delivery_status']+"+email+wap"
            #     )



EMAIL_NOTIFICATION_SERVICE = EmailNotificationService()