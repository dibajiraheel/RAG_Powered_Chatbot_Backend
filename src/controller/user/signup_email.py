from api_models.singup import SignupRequest
from sqlalchemy.orm import Session
from db_models.user_model import User
from api_models.response import APIResponse
from utils.bcrypt_password import encrypt_password

async def signup_using_email_controller(session: Session, userdata: SignupRequest) -> APIResponse:
    user_found = session.query(User).filter_by(email = userdata.email).first()
    if user_found:
        response = APIResponse(task_completed=False, detail='email already registered', status_code=400)
        return response
    
    username_found = session.query(User).filter_by(username = userdata.username).first()
    if username_found:
        response = APIResponse(task_completed=False, detail='username already registered', status_code=400)
        return response
    
    hashed_password = encrypt_password(userdata.password)
    new_user = User(username = userdata.username, email = userdata.email, password = hashed_password, profile_pic_url = getattr(userdata, 'profile_pic_url', None), registered_using = 'email')

    session.add(new_user)
    session.commit()

    response = APIResponse(task_completed=True, detail = 'successfull', status_code = 201)
    return response

