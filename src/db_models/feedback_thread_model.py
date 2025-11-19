from sqlalchemy import String, ForeignKey
from db_connection.db_base import DBClass
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Feedback(DBClass):
    __tablename__ = 'feedbacks'

    thread_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    user: Mapped['User'] = relationship(back_populates='feedbacks')

