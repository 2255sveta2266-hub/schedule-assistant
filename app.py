import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from parser.updater import run_auto_update
from bot.vk_bot import run_bot

if __name__ == "__main__":
    print("=== Запуск Schedule Assistant ===")

    # Запускаем обновление расписания в фоне — бот стартует сразу не ожидая
    run_auto_update()

    # Запускаем VK бота
    run_bot()