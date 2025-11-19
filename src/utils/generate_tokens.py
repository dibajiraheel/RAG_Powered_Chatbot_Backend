from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import config
from utils.tokens_model import TokenData

def generate_access_token(data_to_encode) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=int(config.access_token_expiry_time_in_minutes))
    jwt_data = {**dict(data_to_encode), 'exp': expires_at}
    access_token = jwt.encode(jwt_data, config.access_token_secret)
    return access_token

def generate_refresh_token(data_to_encode) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=int(config.refresh_token_expiry_time_in_minutes))
    jwt_data = {**dict(data_to_encode), 'exp': expires_at}
    refresh_token = jwt.encode(jwt_data, config.refresh_token_secret)
    return refresh_token

def generate_both_tokens(data_to_encode) -> str:
    access_token = generate_access_token(data_to_encode)
    refresh_token = generate_refresh_token(data_to_encode)
    return access_token, refresh_token

def decode_access_token(access_token):
    try:
        data = jwt.decode(access_token, config.access_token_secret)
        data_object = TokenData(**data)
        return data_object
    except JWTError:
        return False

def decode_refresh_token(refresh_token):
    try:
        data = jwt.decode(refresh_token, config.refresh_token_secret)
        data_object = TokenData(**data)
        return data_object
    except JWTError:
        return False
    

    