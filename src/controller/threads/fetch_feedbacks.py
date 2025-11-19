from sqlalchemy.orm import Session
from utils.tokens_model import TokenData
from api_models.fetch_feedbacks_response import APIFetchFeedbackResponse
from db_models.feedback_thread_model import Feedback
from db_models.user_model import User



async def fetch_feedback_controller(userinfo: TokenData, session: Session) -> APIFetchFeedbackResponse:
    userdata = session.query(User).filter_by(email = userinfo.email).first()
    if not userdata:
        response = APIFetchFeedbackResponse(task_completed=False, detail=['email not registered'], status_code=400)
        return response
    threads = session.query(Feedback).filter_by(user_id = userdata.id).all()
    # print('FEEDBACKS = ', threads)
    threads_to_send = []
    for thread in threads:
        threads_to_send.append(thread.thread_id)
    response = APIFetchFeedbackResponse(task_completed=True, detail=threads_to_send, status_code=200)
    return response














