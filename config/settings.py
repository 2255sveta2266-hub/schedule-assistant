from dotenv import load_dotenv
import os

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID", "239798994"))

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_VECTOR_STORE_ID = os.getenv("YANDEX_VECTOR_STORE_ID")

# Устаревшее ??
YANDEX_ASSISTANT_ID = os.getenv("YANDEX_ASSISTANT_ID")