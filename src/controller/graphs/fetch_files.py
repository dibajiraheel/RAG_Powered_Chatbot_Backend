from sqlalchemy.orm import Session
from db_models.user_model import User
from db_models.file_model import File
from api_models.fetch_files_response import APIFetchFilesResponse
from utils.tokens_model import TokenData



async def fetch_files_controller(userinfo: TokenData, session: Session):
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        response = APIFetchFilesResponse(task_completed=False, detail=['email not registered'], status_code=400)
        return response
    files = session.query(File).filter_by(user_id = userdata.id).all()
    
    if not files:
        response = APIFetchFilesResponse(task_completed=True, detail=[], status_code=200)

    files_to_send = []
    for file in files:
        file_to_send = {'id': file.id, 'filename': file.file_name}
        files_to_send.append(file_to_send)
    
    response = APIFetchFilesResponse(task_completed=True, detail=files_to_send, status_code=200)
    return response

