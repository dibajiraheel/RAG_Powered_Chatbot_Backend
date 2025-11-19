from sqlalchemy.orm import Session
from api_models.response import APIResponse
from db_models.user_model import User
from utils.generate_tokens import decode_refresh_token, generate_both_tokens
from utils.tokens_model import TokenData


async def retrieve_access_token_controller(session: Session, email: str) -> APIResponse:
    userdata = session.query(User).filter_by(email = email).first()
    if not userdata:
        response = APIResponse(task_completed=True, detail=['email not registered'], status_code=400)
        return response
    
    refresh_token = userdata.refresh_token
    decoded_refresh_token = decode_refresh_token(refresh_token=refresh_token)
    if not decoded_refresh_token:
        response = APIResponse(task_completed=True, detail=['invalid/expired refresh token'], status_code=400)
        return response
    # print('DECODED REFRESH TOKEN', decoded_refresh_token)
    # print('REGISTERED USING FROM DECODED REFRESH TOKEN = ', decoded_refresh_token.registered_using)
    data_to_encode = TokenData(username=decoded_refresh_token.username, email=decoded_refresh_token.email, profile_pic_url=getattr(decoded_refresh_token, 'profile_pic_url', ''), registered_using=decoded_refresh_token.registered_using)
    new_access_token, new_refresh_token = generate_both_tokens(data_to_encode=data_to_encode)

    userdata.refresh_token = new_refresh_token
    session.commit()

    response = APIResponse(task_completed=True, detail=['successfully retrieved access token', new_access_token], status_code=200)
    return response
