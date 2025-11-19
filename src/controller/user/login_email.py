from sqlalchemy.orm import Session
from db_models.user_model import User
from api_models.login_response import APILoginResponse
from api_models.login import LoginRequest
from utils.bcrypt_password import verify_password
from utils.generate_tokens import generate_both_tokens
from utils.tokens_model import TokenData



async def login_using_email_controller(session: Session, userdata: LoginRequest) -> APILoginResponse:
    user_found = session.query(User).filter_by(email = userdata.email).first()
    if not user_found:
        response = APILoginResponse(task_completed=False, detail=['email not registered'], status_code=400)
        return response
    # print('userfound', user_found)
    # print('userfound password', user_found.password)
    is_password_verified = verify_password(str(userdata.password), user_found.password)
    if not is_password_verified:
        response = APILoginResponse(task_completed = False, detail=['email or password is incorrect'], status_code = 400)
        return response
    
    profile_pic_url = user_found.profile_pic_url
    username = user_found.username
    email = user_found.email

    data_to_encode = TokenData(username = user_found.username, email = user_found.email, profile_pic_url = getattr(user_found, 'profile_pic_url', ''), registered_using = user_found.registered_using)
    access_token, refresh_token = generate_both_tokens(data_to_encode)

    user_found.refresh_token = refresh_token
    session.commit()
    
    response = APILoginResponse(task_completed = True, detail = [access_token, profile_pic_url, username, email], status_code = 200)
    return response





