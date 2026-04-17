from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
import os
from rest_framework.response import Response
from rest_framework import status
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

class BrevoEmailService:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        template_dir = os.path.join(BASE_DIR, 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        self.configuration = Configuration()
        self.configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")
        self.api_instance = TransactionalEmailsApi(ApiClient(self.configuration))
        
    def render_html(self, template_name, **context):
        template = self.env.get_template(template_name)
        return template.render(**context)

    def send(self, subject: str, body: str, recipient: str, is_html=False):
        sender_email="konversaai@gmail.com"
        sender_name="Konversa"
        
        content_field = "html_content" if is_html else "text_content"

        email_data = {
            "to": [{"email": recipient}],
            "sender": {"email": sender_email, "name": sender_name},
            "subject": subject,
            content_field: body,
        }
        
        try:
            email = SendSmtpEmail(**email_data) 
            return self.api_instance.send_transac_email(email)
        
        except Exception as e:
            print(f"Email send failed: {e}")
            return Response({"detail": str(e), "status": "error"}, status=status.HTTP_400_BAD_REQUEST)
        
    def send_html(self, subject: str, template_path: str, recipient: str, context):
        base_url = os.getenv("SERVICE_BASE_URL")
        context['base_url'] = base_url
        
        html_content = self.render_html(template_path, **context)
        
        return self.send(subject, html_content, recipient, is_html=True)