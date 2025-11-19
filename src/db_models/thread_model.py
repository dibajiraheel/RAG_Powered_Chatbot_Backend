from sqlalchemy import String, ForeignKey
from db_connection.db_base import DBClass
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Thread(DBClass):
    __tablename__ = 'threads'

    thread_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=False)

    user: Mapped['User'] = relationship(back_populates='threads')

