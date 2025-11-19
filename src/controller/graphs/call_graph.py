from utils.tokens_model import TokenData
from sqlalchemy.orm import Session
from uuid import uuid4
from controller.threads.add_thread import add_thread_controller
from api_models.call_graph_response import APICallGraphResponse
from db_models.file_model import File
from db_models.user_model import User
from fastapi import HTTPException
from db_models.feedback_thread_model import Feedback


import files_to_load.config_to_load as config_to_load_at_initialization


async def call_graph_controller(question: str, call_which_subgraph: str, thread_id: str, userinfo: TokenData, file_names: list[str], session: Session) -> APICallGraphResponse:
    
    # print('THREAD ID = ', thread_id)
    # print('QUESTION = ', question)
    # print('CALL WHICH SUBGRAPH = ', call_which_subgraph)
    # print("FILES NAMES = ", file_names)
    add_thread_id = False
    if not thread_id:
        add_thread_id = True
        thread_id = uuid4()
        thread_config = {'configurable': {'thread_id': str(thread_id)}}
    else:
        thread_config = {'configurable': {'thread_id': str(thread_id)}}

    small_documents_ids = []
    large_documents_ids = []
    files_data = ''
    files_data_dict = {}
    files_small_documents_ids = {}
    files_large_documents_ids = {}
    # print('FILENAMES RECEIVED IN CONTROLLER = ', file_names)
    if file_names:
        userdata = session.query(User).filter_by(email = userinfo.email).first()
        # print('USER DATA FOUND = ', userdata)
        if not userdata:
            raise HTTPException(status_code=400, detail='email not registered')
        for index, file_name in enumerate(file_names):
            filesdata = session.query(File).filter_by(file_name = file_name).filter_by(user_id = userdata.id).all()
            for filedata in filesdata:
                # print('FILE DATA = ', filedata)
                small_document_ids = filedata.small_document_ids
                large_document_ids = filedata.large_document_ids
                file_small_documents_ids = []
                file_large_documents_ids = []
                
                for small_document_id in small_document_ids:
                    small_documents_ids.append(small_document_id)
                    file_small_documents_ids.append(small_document_id)
                
                for large_document_id in large_document_ids:
                    large_documents_ids.append(large_document_id)
                    file_large_documents_ids.append(large_document_id)

                files_large_documents_ids[file_name] = file_large_documents_ids
                files_small_documents_ids[file_name] = file_small_documents_ids

                file_data = f'''
                            ______________________________________________________
                            File No: {index + 1}
                            File Name: {filedata.file_name}
                            Title: {filedata.title}
                            Authors: {filedata.authors}
                            Topic: {filedata.document_topic}
                            File Type: {filedata.document_type}
                            Publication Date: {filedata.publication_date}
                            _______________________________________________________________
                            '''
                files_data = files_data + file_data

                file_data_dict = {
                    'file_no': index + 1,
                    'file_name': filedata.file_name,
                    'title': filedata.title,
                    'authors': filedata.authors,
                    'topic': filedata.document_topic,
                    'file_type': filedata.document_type,
                    'publication_date': filedata.publication_date
                }
                files_data_dict[file_name] = file_data_dict

    graph_response = config_to_load_at_initialization.COMPILED_MAIN_GRAPH.invoke({
        'question': question,
        'call_which_subgraph': call_which_subgraph,
        'small_document_ids': small_documents_ids,
        'large_document_ids': large_documents_ids,
        'files_large_documents_ids': files_large_documents_ids,
        'files_small_documents_ids': files_small_documents_ids,
        'files_data_dict': files_data_dict,
        'files_data': files_data 
    }, config=thread_config)
    # print('COMPLETE RESPONSE OF GRAPH = ', graph_response)

    if add_thread_id:
        thread_id = str(thread_id)
        thread_added = await add_thread_controller(session = session, thread_id = thread_id, title = question, userinfo = userinfo)
        if not thread_added:
            response = APICallGraphResponse(task_completed=False, detail='unable to add thread id in database', status_code=500, thread_id='')
            return response
    
    if call_which_subgraph == 'general':
        response = APICallGraphResponse(task_completed=True, detail=graph_response['response'].content, status_code=200, thread_id=thread_id)
        return response

    elif call_which_subgraph == 'rag':
        
        interrupt_present_in_rag_response = graph_response.get('__interrupt__', '')
        # print('INTERRUPT PRESENT = ', bool(interrupt_present_in_rag_response))
        if graph_response['answer_provided'] and (not bool(interrupt_present_in_rag_response)):
            response = APICallGraphResponse(task_completed=True, detail=graph_response['response'].content, status_code=200, thread_id=thread_id)
            return response
        elif (not graph_response['answer_provided']) and (bool(interrupt_present_in_rag_response)):
            interrupt_present = interrupt_present_in_rag_response[0]
            try:
                thread_to_add_in_feedback = Feedback(thread_id=thread_id, user=userdata)
                session.add(thread_to_add_in_feedback)
                session.commit()
            except Exception as e:
                response = APICallGraphResponse(task_completed=False, detail=e, status_code=500)
                return response
            response = APICallGraphResponse(task_completed=True, detail=interrupt_present.value, status_code=200, thread_id=thread_id)
            return response
        



    

    
        