from services.schedule_service import get_schedule_by_group

lessons = get_schedule_by_group("АСУб-25-1")

print("Найдено записей:", len(lessons))

for lesson in lessons[:5]:
    print(
        lesson.subject,
        lesson.teacher,
        lesson.time_start,
        lesson.room
    )