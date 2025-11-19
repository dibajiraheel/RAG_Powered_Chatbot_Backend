import smtplib
from api_models.email_response import EmailResponse


def send_mail(sender_email: str, sender_email_app_password: str, receiver_email: str, email_content: str) -> EmailResponse:
    try:
        with smtplib.SMTP('smtp.gmail.com', port = 587) as server:
            server.starttls()

            server.login(sender_email, sender_email_app_password)
            server.sendmail(sender_email, receiver_email, email_content)
            email_response = EmailResponse(email_sent=True)
            return email_response
    except Exception as e:
        email_response = EmailResponse(email_sent=False, detail=str(e))
        return email_response
    



    