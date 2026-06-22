from database.db_manager import SessionLocal
from database.models import User


def add_user(user_id: str, name: str):
    session = SessionLocal()

    existing_user = (
        session.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not existing_user:
        user = User(
            user_id=user_id,
            name=name
        )

        session.add(user)
        session.commit()

    session.close()


def get_all_users():
    session = SessionLocal()

    users = session.query(User).all()

    session.close()

    return users