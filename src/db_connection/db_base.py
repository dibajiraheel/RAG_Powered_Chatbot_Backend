from sqlalchemy import create_engine, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from datetime import datetime



Base = declarative_base()


class DBClass(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
