from fastapi import APIRouter, status, Depends, HTTPException, Request, File, UploadFile
from fastapi.security import OAuth2PasswordBearer
from api_models.singup import SignupRequest
from api_models.login import LoginRequest
from api_models.response import APIResponse
# from db_connection.db import initialize_db, get_db_session
from sqlalchemy.orm import Session
from controller.user.signup_email import signup_using_email_controller
from controller.user.login_email import login_using_email_controller
from utils.tokens_model import TokenData
from utils.generate_tokens import decode_access_token
from api_models.send_otp import SendOtp
from controller.user.send_otp import send_otp_controller
from api_models.verify_otp import VerifyOtp
from controller.user.verify_otp import verify_otp_controller
from api_models.update_password import UpdatePassword
from controller.user.update_password import update_password_controller
from controller.user.upload_profile_pic import upload_profile_pic_controller
from utils.tokens_model import TokenData
from api_models.login_response import APILoginResponse
from controller.user.retrieve_access_token import retrieve_access_token_controller

from files_to_load.config_to_load import get_db_session


user_router = APIRouter()

oauth2 = OAuth2PasswordBearer(tokenUrl = '/user/login')

def get_user_details(access_token = Depends(oauth2)) -> TokenData:
    userinfo = decode_access_token(access_token)
    if not userinfo:
        raise HTTPException(status_code=400, detail='invalid/expired access token')
    return userinfo

@user_router.post('/signup-email', status_code=status.HTTP_201_CREATED)
async def signup_email_route(request: Request, session = Depends(get_db_session)) -> APIResponse:
    formdata = SignupRequest(**dict(await request.form()))
    response = await signup_using_email_controller(session = session, userdata = formdata)
    if not response.task_completed:
        raise HTTPException(status_code=400, detail=response.detail)
    return response

@user_router.post('/login-email', status_code=status.HTTP_200_OK)
async def login_email_route(request: Request, session = Depends(get_db_session)) -> APILoginResponse:
    formdata = LoginRequest(**dict(await request.form()))
    response = await login_using_email_controller(session = session, userdata = formdata)
    if not response.task_completed:
        raise HTTPException(status_code=400, detail=response.detail[0])
    return response

@user_router.post('/send-otp', status_code=status.HTTP_200_OK)
async def send_otp_route(request: Request, session = Depends(get_db_session)) -> APIResponse:
    formdata = SendOtp(**dict(await request.form()))
    email = formdata.email
    response = await send_otp_controller(session = session, email = email)
    return response

@user_router.post('/verify-otp', status_code=status.HTTP_200_OK)
async def verify_otp_route(request: Request, session = Depends(get_db_session)) -> APIResponse:
    formdata = VerifyOtp(**dict(await request.form()))
    email = formdata.email
    otp = formdata.otp
    response = await verify_otp_controller(session = session, email = email, otp = otp)
    return response

@user_router.post('/update-password', status_code=status.HTTP_200_OK)
async def update_password_route(request: Request, session = Depends(get_db_session)) -> APIResponse:
    formdata = UpdatePassword(**dict(await request.form()))
    email = formdata.email
    password = formdata.password
    response = await update_password_controller(session = session, email = email, password = password)
    return response

@user_router.post('/update-profile-pic', status_code=status.HTTP_200_OK)
async def update_profile_pic_route(image: UploadFile = File(), session: Session = Depends(get_db_session), userinfo: TokenData = Depends(get_user_details)) -> APIResponse:
    # print('IMAGE CONTENT TYPE = ', image.content_type)
    response = await upload_profile_pic_controller(session = session, image = image, userinfo = userinfo)
    return response

@user_router.get('/retrieve-access-token/{email}', status_code=status.HTTP_200_OK)
async def retrieve_access_token(email: str, session: Session = Depends(get_db_session)) -> APIResponse:
    response = await retrieve_access_token_controller(session = session, email = email)
    return response


    


