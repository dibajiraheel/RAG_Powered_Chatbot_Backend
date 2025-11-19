from db_models.file_model import File
from db_models.user_model import User
from api_models.response import APIResponse
from sqlalchemy.orm import Session
from utils.tokens_model import TokenData




async def user_documents_controller(userinfo: TokenData, session: Session) -> APIResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        return APIResponse(task_completed=False, detail='email not registered', status_code=400)
    user_documents = session.query(File).filter_by(user_id = userdata.id)
    file_names = ''
    for user_document in user_documents:
        file_names = file_names + user_document.file_name + ', '
    return APIResponse(task_completed = True, detail = file_names, status_code = 200)