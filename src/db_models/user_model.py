from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db_connection.db_base import DBClass


class User(DBClass):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    profile_pic_url: Mapped[str] = mapped_column(String, nullable=True)
    profile_pic_public_id: Mapped[str] = mapped_column(String, nullable=True)
    registered_using: Mapped[str] = mapped_column(String, nullable=True)
    otp_generated: Mapped[str] = mapped_column(String, nullable=True)
    otp_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    access_token: Mapped[str] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str] = mapped_column(String, nullable=True)

    files: Mapped[list['File']] = relationship(back_populates='user')
    threads: Mapped[list['Thread']] = relationship(back_populates='user')
    feedbacks: Mapped[list['Feedback']] = relationship(back_populates='user')