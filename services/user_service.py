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
            name=name,
            group_name="",
            state="waiting_for_group"   # новый пользователь — ждём группу
        )
        session.add(user)
        session.commit()

    session.close()


def get_user(user_id: str):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == user_id).first()
    session.close()
    return user


def set_user_group(user_id: str, group_name: str):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == user_id).first()
    if user:
        user.group_name = group_name
        user.state = ""
        session.commit()
    session.close()


def set_user_state(user_id: str, state: str):
    session = SessionLocal()
    user = session.query(User).filter(User.user_id == user_id).first()
    if user:
        user.state = state
        session.commit()
    session.close()


def get_all_users():
    session = SessionLocal()
    users = session.query(User).all()
    session.close()
    return users