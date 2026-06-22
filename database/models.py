from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    answer = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Schedule(Base):
    __tablename__ = "schedule"

    id = Column(Integer, primary_key=True)
    group_name = Column(String, nullable=False)
    teacher = Column(String)
    subject = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time_start = Column(String)
    time_end = Column(String)
    room = Column(String)