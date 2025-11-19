from sqlalchemy.orm import Session
from db_models.user_model import User
from api_models.response import APIResponse
from utils.bcrypt_password import encrypt_password



async def update_password_controller(session: Session, email: str, password: str):
    userdata = session.query(User).filter_by(email = email).first()
    if not userdata:
        response = APIResponse(task_completed=False, detail='email not registered', status_code=400)
        return response
    if not(userdata.otp_verified):
        response = APIResponse(task_completed=False, detail='otp is not verified', status_code=400)
        return response

    encrypted_password = encrypt_password(password)
    userdata.password = encrypted_password
    userdata.otp_generated = None
    userdata.otp_verified = False
    session.commit()
    
    response = APIResponse(task_completed=True, detail='password updated successfully', status_code=200)
    return response
