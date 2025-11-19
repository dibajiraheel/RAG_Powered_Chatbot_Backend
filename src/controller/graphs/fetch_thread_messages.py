from sqlalchemy.orm import Session
from api_models.fetch_thread_messages_response import APIFetchThreadMessagesResponse
from langchain_core.messages import AIMessage, HumanMessage
from db_models.user_model import User
from db_models.thread_model import Thread
from utils.tokens_model import TokenData
from fastapi import HTTPException

import files_to_load.config_to_load as config_to_load_at_initialization

async def fetch_thread_messages_controller(session: Session, thread_id: str, userinfo: TokenData) -> APIFetchThreadMessagesResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        raise HTTPException(status_code=400, detail='email not registered')
    
    user_threads = session.query(Thread).filter_by(user_id = userdata.id).all()
    # print('TYPE OF USER THREADS RECEVIED FROM DB = ', type(user_threads))
    
    thread_found_in_db = False
    for user_thread in user_threads:
        if user_thread.thread_id == thread_id:
            thread_found_in_db = True

    if not thread_found_in_db:
        raise HTTPException(status_code=400, detail='thread id not found associated with current user')

    try:
        config = {'configurable': {'thread_id': thread_id}}
    
        state = config_to_load_at_initialization.COMPILED_MAIN_GRAPH.get_state(config = config).values
        conversational_messages = state['all_messages']
        # print('STATE = ', state['all_messages'])
        conversational_messages_list = []
        for conversational_message in conversational_messages:
            if isinstance(conversational_message, HumanMessage):
                message_to_append = ('human', conversational_message.content)
                conversational_messages_list.append(message_to_append)
            elif isinstance(conversational_message, AIMessage):
                message_to_append = ('ai', conversational_message.content)
                conversational_messages_list.append(message_to_append)
        
        response = APIFetchThreadMessagesResponse(task_completed=True, detail='success', status_code=200, thread_messages=conversational_messages_list)
        return response
    except:
        response = APIFetchThreadMessagesResponse(task_completed=False, detail='no conversation found with provided thread id', status_code=400, thread_messages=[])
        return response
    


    