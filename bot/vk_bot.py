import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from assistant.yandex_assistant import process_message


TOKEN = "vk1.a.uJHUfxejRT0u39UvZNiAj8nWAODf4oxTBiPqLbxO40sGYXY8kVbhX7geWhVBHNtKwBYZWt3YvR_-1K-eTibipmhYLMpztQx4Zx3FATvr5-4os200pCaYY3Kq--Re9wJZf4P46Xv_bhHomkAo9KE0vUUoP2okuClyC6EYADiMEC0kw4otwc-F5GjuoBcZA_gsiW510D4uxZGk_nd_FGrOIw"
GROUP_ID = 239798994


vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

print("VK BOT STARTED ")


def send_message(peer_id, text):
    vk.messages.send(
        peer_id=peer_id,
        message=text,
        random_id=0
    )


for event in longpoll.listen():

    if event.type == VkBotEventType.MESSAGE_NEW:

        message = event.object.message["text"]
        peer_id = event.object.message["peer_id"]

        print("Получено сообщение:", message)

        response = process_message(message)

        print("Ответ:", response)

        send_message(peer_id, response)