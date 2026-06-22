from database.db_manager import SessionLocal
from database.models import Schedule


def add_schedule(
    group_name,
    teacher,
    subject,
    date,
    time_start,
    time_end,
    room
):
    session = SessionLocal()

    lesson = Schedule(
        group_name=group_name,
        teacher=teacher,
        subject=subject,
        date=date,
        time_start=time_start,
        time_end=time_end,
        room=room
    )

    session.add(lesson)
    session.commit()

    session.close()


def get_schedule_by_group(group_name):
    session = SessionLocal()

    lessons = (
        session.query(Schedule)
        .filter(Schedule.group_name == group_name)
        .all()
    )

    session.close()

    return lessons


def get_schedule_by_date(date):
    session = SessionLocal()

    lessons = (
        session.query(Schedule)
        .filter(Schedule.date == date)
        .all()
    )

    session.close()

    return lessons


def clear_schedule():
    session = SessionLocal()

    session.query(Schedule).delete()

    session.commit()

    session.close()