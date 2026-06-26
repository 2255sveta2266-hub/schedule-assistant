from database.db_manager import SessionLocal
from database.models import Schedule


def add_schedule(group_name, teacher, subject, date, time_start, time_end, room, subgroup=""):
    session = SessionLocal()
    lesson = Schedule(
        group_name=group_name,
        teacher=teacher,
        subject=subject,
        date=date,
        time_start=time_start,
        time_end=time_end,
        room=room,
        subgroup=subgroup
    )
    session.add(lesson)
    session.commit()
    session.close()


def get_schedule_by_group(group_name):
    session = SessionLocal()
    lessons = (
        session.query(Schedule)
        .filter(Schedule.group_name == group_name)
        .order_by(Schedule.date, Schedule.time_start)
        .all()
    )
    session.close()
    return lessons


def get_schedule_by_date(date):
    session = SessionLocal()
    lessons = (
        session.query(Schedule)
        .filter(Schedule.date == date)
        .order_by(Schedule.time_start)
        .all()
    )
    session.close()
    return lessons


def get_schedule_by_teacher(teacher):
    session = SessionLocal()
    lessons = (
        session.query(Schedule)
        .filter(Schedule.teacher.contains(teacher))
        .order_by(Schedule.date, Schedule.time_start)
        .all()
    )
    session.close()
    return lessons


def get_schedule_by_group_and_date(group_name: str, date: str):
    session = SessionLocal()
    lessons = (
        session.query(Schedule)
        .filter(Schedule.group_name == group_name, Schedule.date == date)
        .order_by(Schedule.time_start)
        .all()
    )
    session.close()
    return lessons


def clear_schedule(group_name=None):
    session = SessionLocal()
    if group_name:
        session.query(Schedule).filter(Schedule.group_name == group_name).delete()
    else:
        session.query(Schedule).delete()
    session.commit()
    session.close()