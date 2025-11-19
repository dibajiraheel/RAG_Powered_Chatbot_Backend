from sqlalchemy.orm import Session
from utils.tokens_model import TokenData
from api_models.fetch_threads_response import APIFetchThreadsResponse
from db_models.thread_model import Thread
from db_models.user_model import User



async def fetch_threads_controller(userinfo: TokenData, session: Session) -> APIFetchThreadsResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        response = APIFetchThreadsResponse(task_completed=False, detail=['email not registered'], status_code=400)
        return response
    threads = session.query(Thread).filter_by(user_id = userdata.id).all()
    # print('THREADS = ', threads)
    # print('TYPE OF THREADS = ', type(threads))
    # print('FIRST THREAD = ', threads[0])
    threads_to_send = []
    for thread in threads:
        thread_to_send = {'thread_id': thread.thread_id, 'title': thread.title}
        threads_to_send.append(thread_to_send)
    response = APIFetchThreadsResponse(task_completed=True, detail=threads_to_send, status_code=200)
    return response














