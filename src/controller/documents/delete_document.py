from sqlalchemy.orm import Session
from api_models.response import APIResponse
from db_models.user_model import User
from db_models.file_model import File
from utils.tokens_model import TokenData

import files_to_load.config_to_load as config_to_load_at_initialization


async def delete_document_controller(file_id: int, userinfo: TokenData, session: Session) -> APIResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        response = APIResponse(task_completed=False, detail='email not registered', status_code=400)
        return response
    
    userdocument = session.query(File).filter_by(user_id = userdata.id).filter_by(id = file_id).first()
    if not userdocument:
        response = APIResponse(task_completed=False, detail='file not found', status_code=400)
        return response

    small_docs_ids = userdocument.small_document_ids
    large_docs_ids = userdocument.large_document_ids

    try:
        config_to_load_at_initialization.SMALL_DOCS_VECTOR_STORE.delete(small_docs_ids)
        config_to_load_at_initialization.LARGE_DOCS_VECTOR_STORE.delete(large_docs_ids)
    except Exception as e:
        response = APIResponse(task_completed=False, detail=e, status_code=500)
        return response

    session.delete(userdocument)
    session.commit()

    response = APIResponse(task_completed=True, detail='file deleted successfully', status_code=200)
    return response





