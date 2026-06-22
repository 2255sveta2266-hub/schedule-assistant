from dotenv import load_dotenv
import os

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")

YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
YANDEX_ASSISTANT_ID = os.getenv("YANDEX_ASSISTANT_ID")