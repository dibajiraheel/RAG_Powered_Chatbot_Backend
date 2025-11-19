from sqlalchemy.orm import Session
from db_models.thread_model import Thread
from db_models.user_model import User
from utils.tokens_model import TokenData
from fastapi import HTTPException


async def add_thread_controller(session: Session, thread_id: str, title: str, userinfo: TokenData) -> bool:
    try:
        userdata = session.query(User).filter_by(email = userinfo.email).first()
        if userdata:
            thread_data = Thread(thread_id = thread_id, title = title, user = userdata)
            session.add(thread_data)
            session.commit()
            return True
        else:
            raise HTTPException(status_code=400, detail='email not registered')
    except Exception as e:
        # print('exception = ', e)
        return False