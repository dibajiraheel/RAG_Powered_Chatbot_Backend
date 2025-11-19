from api_models.call_graph_response import APICallGraphResponse
from utils.tokens_model import TokenData
from langgraph.types import Command
from db_models.feedback_thread_model import Feedback
from sqlalchemy.orm import Session
from db_models.user_model import User

import files_to_load.config_to_load as config_to_load_at_initialization


async def resume_graph_controller(userinfo: TokenData, thread_id: str, human_feedback: str, session: Session) -> APICallGraphResponse:
     
    userdata = session.query(User).filter_by(email=userinfo.email).first()
    if not userdata:
        response = APICallGraphResponse(task_completed=False, detail='email not registered', status_code=400)
        return response
    
    thread_data = session.query(Feedback).filter_by(user_id=userdata.id).filter_by(thread_id=thread_id).first()
    if not thread_data:
        response = APICallGraphResponse(task_completed=False, detail='thread not found', status_code=400)
    
    config = {'configurable': {'thread_id': thread_id}}
   
    graph_response = config_to_load_at_initialization.COMPILED_MAIN_GRAPH.invoke(Command(resume=human_feedback), config=config)
    # print('COMPLETE RESPONSE OF GRAPH = ', graph_response)

    session.delete(thread_data)
    session.commit()

    response = APICallGraphResponse(task_completed=True, detail=graph_response['response'].content, status_code=200, thread_id=thread_id)
    return response















    