from sqlalchemy.orm import Session
from api_models.response import APIResponse
from db_models.user_model import User
from fastapi import HTTPException
from utils.generate_otp import generate_otp
from utils.send_mail import send_mail
from config import config


async def send_otp_controller(session: Session, email: str) -> APIResponse:
    userdata = session.query(User).filter_by(email = email).first()
    if not userdata:
        raise HTTPException(status_code=400, detail='email not registered')
    otp_generated = generate_otp(characters=8)
    content = f'OTP TO RESET YOUR PASSWORD IS {otp_generated}'
    email_response = send_mail(sender_email=config.otp_gmail, sender_email_app_password=config.otp_gmail_app_password, receiver_email=userdata.email, email_content=content)
    if not email_response.email_sent:
        response = APIResponse(task_completed=False, detail=email_response.detail, status_code=500)
        return response
    userdata.otp_generated = otp_generated
    session.commit()
    response = APIResponse(task_completed=True, detail='otp sent successfully', status_code=200)
    return response










