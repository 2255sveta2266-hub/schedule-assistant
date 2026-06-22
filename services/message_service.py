from database.db_manager import SessionLocal
from database.models import Message


def save_message(user_id: str, message: str, answer: str):
    session = SessionLocal()

    new_message = Message(
        user_id=user_id,
        message=message,
        answer=answer
    )

    session.add(new_message)
    session.commit()

    session.close()


def get_all_messages():
    session = SessionLocal()

    messages = session.query(Message).all()

    session.close()

    return messages