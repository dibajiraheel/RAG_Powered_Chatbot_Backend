from sqlalchemy.orm import Session
from db_models.user_model import User
from db_models.thread_model import Thread
from utils.tokens_model import TokenData
from api_models.response import APIResponse
from langgraph.checkpoint.postgres import PostgresSaver

import files_to_load.config_to_load as config_to_load_at_initialization


async def delete_thread_controller(userinfo: TokenData, session: Session, thread_id: str) -> APIResponse:
    userdata = session.query(User).filter_by(email=userinfo.email).first()
    if not userdata:
        response = APIResponse(task_completed=False, detail='email not registered', status_code=400)
        return response
    
    user_thread = session.query(Thread).filter_by(user_id=userdata.id).filter_by(thread_id=thread_id).first()
    if not user_thread:
        response = APIResponse(task_completed=False, detail='thread with provided thread id not found in all threads associated with this user threads data', status_code=400)
        return response

    # print('THREAD FOUND = ', thread_id, 'AND NOW DELETING IT')
    try:
        config_to_load_at_initialization.POSTGRES_CHECKPOINTER.delete_thread(thread_id=thread_id)
    except Exception as e:
        response = APIResponse(task_completed=False, detail=e, status_code=500)
        return response
    print("THREAD DELETED SUCCESSFULLY.")

    session.delete(user_thread)
    session.commit()

    response = APIResponse(task_completed=True, detail='thread deleted successfully', status_code=200)
    return response


















