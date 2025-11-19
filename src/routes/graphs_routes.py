from api_models.response import APIResponse
from fastapi import APIRouter, status, Depends, Request, Query
# from db_connection.db import get_db_session
from sqlalchemy.orm import Session
from utils.tokens_model import TokenData
from routes.user_routes import get_user_details
from controller.graphs.call_graph import call_graph_controller
from api_models.call_graph import CallGraph
from api_models.fetch_thread_messages_response import APIFetchThreadMessagesResponse
from controller.graphs.fetch_thread_messages import fetch_thread_messages_controller
from api_models.call_graph_response import APICallGraphResponse
from typing import Optional
from controller.graphs.resume_graph import resume_graph_controller
from typing import Literal
from api_models.fetch_threads_response import APIFetchThreadsResponse
from controller.threads.fetch_threads import fetch_threads_controller
from api_models.fetch_files_response import APIFetchFilesResponse
from controller.graphs.fetch_files import fetch_files_controller
from controller.threads.delete_thread import delete_thread_controller
from api_models.fetch_feedbacks_response import APIFetchFeedbackResponse
from controller.threads.fetch_feedbacks import fetch_feedback_controller

from files_to_load.config_to_load import get_db_session


graphs_routes = APIRouter()


@graphs_routes.post('/call-graph', status_code=status.HTTP_200_OK)
async def call_graph(request: Request, userinfo: TokenData = Depends(get_user_details), thread_id: Optional[str] = None, file_names: Optional[list[str]] = Query(None), session: Session = Depends(get_db_session)) -> APICallGraphResponse:
    call_graph_data = CallGraph(**(dict(await request.form())))
    # print('CALL GRAPH DATA RECEIVED = ', call_graph_data)
    question = call_graph_data.question
    call_which_subgraph = call_graph_data.call_which_subgraph
    response = await call_graph_controller(question = question, call_which_subgraph = call_which_subgraph, thread_id = thread_id, userinfo = userinfo, file_names = file_names, session = session)
    return response


@graphs_routes.get('/fetch-threads', status_code = status.HTTP_200_OK)
async def fetch_threads(userinfo: TokenData = Depends(get_user_details), session = Depends(get_db_session)) -> APIFetchThreadsResponse:
    response = await fetch_threads_controller(userinfo = userinfo, session = session)
    return response

@graphs_routes.get('/fetch-files', status_code=status.HTTP_200_OK)
async def fetch_files(userinfo: TokenData = Depends(get_user_details), session = Depends(get_db_session)) -> APIFetchFilesResponse:
    response = await fetch_files_controller(userinfo = userinfo, session = session)
    return response


@graphs_routes.get('/fetch-thread-messages/{thread_id}', status_code=status.HTTP_200_OK)
async def fetch_conversation(thread_id: str, userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)) -> APIFetchThreadMessagesResponse:
    response = await fetch_thread_messages_controller(session = session, thread_id = thread_id, userinfo = userinfo)
    return response


@graphs_routes.get('/fetch-feedbacks', status_code=status.HTTP_200_OK)
async def fetch_feedbacks(userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)) -> APIFetchFeedbackResponse:
    response = await fetch_feedback_controller(userinfo=userinfo, session=session)
    return response


@graphs_routes.delete('/delete-thread/{thread_id}', status_code=status.HTTP_200_OK)
async def delete_thread(thread_id: str, userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)) -> APIResponse:
    response = await delete_thread_controller(userinfo=userinfo, session=session, thread_id=thread_id)
    return response

@graphs_routes.post('/resume-graph', status_code=status.HTTP_200_OK)
async def resume_graph(thread_id: str, human_feedback: Optional[Literal['yes', 'no']] = 'no', userinfo: TokenData = Depends(get_user_details), session: Session = Depends(get_db_session)) -> APICallGraphResponse:
    response = await resume_graph_controller(userinfo = userinfo, thread_id = thread_id, human_feedback = human_feedback, session = session)
    return response



