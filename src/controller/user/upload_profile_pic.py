from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from api_models.response import APIResponse
from db_models.user_model import User
import tempfile
import shutil
import os
from utils.upload_file_on_cloudinary import upload_file_on_cloudinary
from utils.tokens_model import TokenData
from fastapi import HTTPException
from utils.delete_file_from_cloudinary import delete_file_from_cloudinary


async def upload_profile_pic_controller(session: Session, image: UploadFile, userinfo: TokenData) -> APIResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        raise HTTPException(status_code=400, detail='email not registered')
    
    if userdata.profile_pic_url and userdata.profile_pic_public_id:
        result = delete_file_from_cloudinary(userdata.profile_pic_public_id)
        if not result:
            response = APIResponse(task_completed=False, detail = 'failed to delete previous profile picture, try again later', status_code=500)
            return response
            
    temp_file_directory = (str(os.getcwd()) + '/temp_files')
    os.makedirs(temp_file_directory, exist_ok=True)
    print('OK IMAGE = ', temp_file_directory)
    with tempfile.NamedTemporaryFile(dir = temp_file_directory, suffix='.jpg', delete=False) as temp_file:
        shutil.copyfileobj(image.file, temp_file)

    temp_file_path = temp_file.name
    result = upload_file_on_cloudinary(file_path = temp_file_path)
    # print('PUBLIC ID = ', result['public_id'])
    # print('SECURE URL = ', result['secure_url'])

    userdata.profile_pic_url = result['secure_url']
    userdata.profile_pic_public_id = result['public_id']
    session.commit()


    response = APIResponse(task_completed=True, detail=['profile pic updated successfully', result['secure_url']], status_code=200)
    return response


    


