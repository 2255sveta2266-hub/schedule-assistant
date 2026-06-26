import sys
import random
import re
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from config.settings import VK_TOKEN, GROUP_ID
from assistant.yandex_assistant import process_message, HELP_TEXT
from services.message_service import save_message
from services.user_service import add_user, get_user, set_user_group, set_user_state
from database.db_manager import create_database


WELCOME_TEXT = """👋 Привет! Я бот-помощник по расписанию ИРНИТУ.

Напиши название своей группы — например: АСУб-25-1
Я запомню её и буду показывать расписание сразу для тебя."""

GROUP_SAVED_TEXT = """✅ Отлично, запомнил группу {group}!

Теперь ты можешь писать:
📆 сегодня — расписание на сегодня
📆 завтра — расписание на завтра
📅 дату: 01.04.2026 — расписание на конкретный день
👨‍🏫 преподаватель Павлова — расписание преподавателя
❓ помощь — список команд"""

NOT_FOUND_GROUP_TEXT = """❌ Группа не найдена.

Проверь название и попробуй ещё раз.
Пример: АСУб-25-1"""


def get_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📆 Сегодня", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📆 Завтра", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📚 Моя группа", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🔄 Сменить группу", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("❓ Помощь", color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def send_message(vk, peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        keyboard=get_keyboard(),
        random_id=random.randint(1, 2**31)
    )


def normalize_group(text: str) -> str:
    """
    Приводим название группы к правильному виду независимо от регистра.
    асуб-25-1 -> АСУб-25-1
    АСУБ-25-1 -> АСУб-25-1
    """
    match = re.match(r"^([А-ЯЁа-яё]+)-(\d{2}-\d+)$", text.strip())
    if not match:
        return text.strip()
    letters = match.group(1)
    digits = match.group(2)
    # Все буквы заглавные кроме последней — она строчная (б, м, и т.д.)
    if len(letters) > 1:
        letters = letters[:-1].upper() + letters[-1].lower()
    return f"{letters}-{digits}"


def is_group_name(text: str) -> bool:
    """Проверяем что текст похож на название группы — нечувствительно к регистру"""
    return bool(re.match(r"^[А-ЯЁа-яё]+-\d{2}-\d+$", text.strip(), re.IGNORECASE))


def normalize(text: str) -> str:
    """Убираем эмодзи и лишние пробелы для сравнения команд"""
    return re.sub(r"[^\w\s]", "", text, flags=re.UNICODE).strip().lower()


def run_bot():
    create_database()

    vk_session = vk_api.VkApi(token=VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)

    print("✅ VK бот запущен. Ожидание сообщений...")

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            message_obj = event.object.message
            message = message_obj["text"].strip()
            peer_id = message_obj["peer_id"]
            from_id = message_obj.get("from_id", peer_id)
            user_id = str(from_id)

            print(f"📨 Сообщение от {peer_id}: {message}")

            try:
                user_info = vk.users.get(user_ids=from_id)
                name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}" if user_info else user_id
            except Exception:
                name = user_id

            add_user(user_id, name)
            user = get_user(user_id)

            msg_norm = normalize(message)

            # --- ЖДЁМ ГРУППУ ---
            if user.state == "waiting_for_group":
                if is_group_name(message):
                    group_normalized = normalize_group(message)
                    from assistant.knowledge_base import find_group_schedule
                    test = find_group_schedule(group_normalized)
                    if "не найдено" in test:
                        response = NOT_FOUND_GROUP_TEXT
                    else:
                        set_user_group(user_id, group_normalized)
                        response = GROUP_SAVED_TEXT.format(group=group_normalized)
                else:
                    response = WELCOME_TEXT

            # --- ОБЫЧНЫЙ РЕЖИМ ---
            else:
                # Кнопка / команда "Сегодня"
                if msg_norm in ("сегодня",):
                    if user.group_name:
                        response = process_message(f"сегодня группа {user.group_name}")
                    else:
                        response = process_message("сегодня")

                # Кнопка / команда "Завтра"
                elif msg_norm in ("завтра",):
                    if user.group_name:
                        response = process_message(f"завтра группа {user.group_name}")
                    else:
                        response = process_message("завтра")

                # Кнопка "Моя группа"
                elif msg_norm in ("моя группа",):
                    if user.group_name:
                        response = f"📚 Твоя группа: {user.group_name}"
                    else:
                        response = "Ты ещё не указал группу. Напиши её название, например: АСУб-25-1"

                # Кнопка "Сменить группу"
                elif msg_norm in ("сменить группу", "изменить группу"):
                    set_user_state(user_id, "waiting_for_group")
                    response = "Напиши название новой группы — например: АСУб-25-1"

                # Кнопка "Помощь"
                elif msg_norm in ("помощь", "help"):
                    response = HELP_TEXT

                # Дата дд.мм.гггг
                elif re.match(r"\d{2}\.\d{2}\.\d{4}", message):
                    if user.group_name:
                        response = process_message(f"{message} группа {user.group_name}")
                    else:
                        response = process_message(message)

                # Пользователь написал название группы — запоминаем
                elif is_group_name(message):
                    group_normalized = normalize_group(message)
                    set_user_group(user_id, group_normalized)
                    response = GROUP_SAVED_TEXT.format(group=group_normalized)

                # Всё остальное
                else:
                    response = process_message(message)

            save_message(user_id, message, response)
            print(f"💬 Ответ: {response[:80]}...")
            send_message(vk, peer_id, response)


if __name__ == "__main__":
    run_bot()