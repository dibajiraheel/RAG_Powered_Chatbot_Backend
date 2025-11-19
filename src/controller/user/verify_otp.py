from sqlalchemy.orm import Session
from fastapi import HTTPException
from db_models.user_model import User
from api_models.response import APIResponse




async def verify_otp_controller(session: Session, email: str, otp: str):
    userdata = session.query(User).filter_by(email = email).first()
    if not userdata:
        raise HTTPException(status_code=400, detail='email not registered')
    if userdata.otp_generated != otp:
        response = APIResponse(task_completed=False, detail='otp is incorrect', status_code=400)
        return response
    
    userdata.otp_verified = True
    session.commit()


    response = APIResponse(task_completed=True, detail='otp is correct', status_code=200)
    return response






