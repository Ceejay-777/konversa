from celery import shared_task

from integrations.email.services import BrevoEmailService

mailer = BrevoEmailService()

@shared_task
def send_signup_otp_email(email, otp):
    mailer.send_html(
        subject="Verify your email",
        template_path="emails/otp_email.html",
        recipient=email,
        context={"otp": otp},
    )