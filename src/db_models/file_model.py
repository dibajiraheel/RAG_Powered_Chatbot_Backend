from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from db_connection.db_base import DBClass
from sqlalchemy.dialects.postgresql import ARRAY



class File(DBClass):
    __tablename__ = 'files'

    file_name: Mapped[str] = mapped_column(String, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    small_document_ids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    large_document_ids: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    authors: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    document_topic: Mapped[str] = mapped_column(String, nullable=False)
    publication_date: Mapped[str] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship(back_populates='files')