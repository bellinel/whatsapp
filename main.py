import httpx
import time
from engine import session, User

# Конфигурация
GREEN_API_ID = '7105218511'  #"7105259866"
GREEN_API_TOKEN = 'fb4cbfa4f35d4141b208cf56b8da429680dc269c41464b3b97'#'2e3c9fbb79db4f8da8fb516fc8c0e5346d44401551cf4e5881'#"
BASE_URL = f"https://7105.api.greenapi.com/waInstance{GREEN_API_ID}"
DELAY = 2

# FSM состояния
STATE_WAIT_NAME = "wait_name"
STATE_WAIT_PHONE = "wait_phone"
STATE_WAIT_PHOTO_FRONT = "wait_photo_front"
STATE_WAIT_PHOTO_BACK = "wait_photo_back"
STATE_DONE = "done"
STATE_WAIT_REGION = "wait_region"
STATE_WAIT_LICENSE_TYPE = "wait_license_type"

# Хранилища
user_states = {}      # chat_id -> state
user_data = {}        # chat_id -> collected data

def reset_user(user_id):
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)

# Получение уведомлений
def get_notification():
    url = f"{BASE_URL}/receiveNotification/{GREEN_API_TOKEN}"
    try:
        response = httpx.get(url, timeout=15)
        # print(response.json())
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print("Ошибка получения:", e)
        return None

# Удаление уведомлений
def delete_notification(receipt_id):
    url = f"{BASE_URL}/deleteNotification/{GREEN_API_TOKEN}/{receipt_id}"
    try:
        httpx.delete(url)
    except:
        pass

# Отправка текста
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "message": text
    }
    try:
        httpx.post(url, json=payload)
    except Exception as e:
        print("Ошибка отправки:", e)


def send_image(chat_id, image_url, caption=""):
    url = f"{BASE_URL}/sendFileByUrl/{GREEN_API_TOKEN}"
    payload = {
        "chatId": chat_id,
        "urlFile": image_url,
        "fileName": "document.jpg",
        "caption": caption
    }
    try:
        httpx.post(url, json=payload)
    except Exception as e:
        print("Ошибка отправки фото:", e)


# FSM логика
def handle_message(user_id, chat_id, message_type, content):
    state = user_states.get(user_id)

    if message_type == "text":
        text = content.strip()

        if text.lower() == "/show":
            users = session.query(User).all()
            if not users:
                send_message(chat_id, "База пуста.")
                return
            for u in users:
                msg = (
                    f"👤 Name: {u.fio}\n"
                    f"📞 Phone: {u.phone}\n"
                    f"🌍 Region: {u.region}\n"
                    f"🎣 License type: {u.license_type}\n"
                    f"🖼 Photo (front): {u.photo_front}\n"
                    f"🖼 Photo (back): {u.photo_back}\n"

                    "———"
                )
                send_message(chat_id, msg)
            return

        if text.lower() == "/start":
            user_states[user_id] = STATE_WAIT_NAME
            user_data[user_id] = {}
            send_message(chat_id, "Bienvenido! Introduce su Nombre y Apellido:")
            return

        if state == STATE_WAIT_NAME:
            user_data[user_id]["fio"] = text
            user_states[user_id] = STATE_WAIT_PHONE
            send_message(chat_id, "Gracias! Ahora introduce su numero de contacto (+34...)")
            return

        elif state == STATE_WAIT_PHONE:
            if not text.replace("+", "").isdigit():
                send_message(chat_id, "Por favor, ingrese un número válido con +34...")
                return
            user_data[user_id]["phone"] = text
            user_states[user_id] = "wait_region"
            send_message(chat_id, "Gracias! Ahora escriba su región (ej: region de murcia , comunidad de madrid ….):")
            return

        elif state == "wait_region":
            user_data[user_id]["region"] = text
            user_states[user_id] = "wait_license_type"
            send_message(chat_id, "Perfecto! Ahora escriba el tipo de licencia (ej: Marina , Dulce):")
            return

        elif state == "wait_license_type":
            user_data[user_id]["license_type"] = text
            user_states[user_id] = STATE_WAIT_PHOTO_FRONT
            send_message(chat_id, "Gracias! Ahora envíe una foto del anverso del documento (DNI/NIE):")
            return

        elif state == STATE_DONE:
            send_message(chat_id, "Registro completado. Escriba /start para solicitar su permiso de pesca!")
            return

        else:
            send_message(chat_id, "Hola! Escriba /start para solicitar tu permiso de pesca!")
            return

    elif message_type == "image":
        url = content

        if state == STATE_WAIT_PHOTO_FRONT:
            user_data[user_id]["photo_front"] = url
            user_states[user_id] = STATE_WAIT_PHOTO_BACK
            send_message(chat_id, "Recibido! Ahora envíe una foto del reverso del documento (DNI/NIE)")
            return

        elif state == STATE_WAIT_PHOTO_BACK:
            user_data[user_id]["photo_back"] = url
            user_states[user_id] = STATE_DONE
            try:
                new_user = User(
                    chat_id=user_id,
                    fio=user_data[user_id]["fio"],
                    phone=user_data[user_id]["phone"],
                    photo_front=user_data[user_id]["photo_front"],
                    photo_back=user_data[user_id]["photo_back"],
                    region=user_data[user_id]["region"],
                    license_type=user_data[user_id]["license_type"]
                )
                session.merge(new_user)
                session.commit()

                send_message(chat_id, "✅Tu solicitud fue enviada con éxito! En breve contactamos con usted!")
                reset_user(user_id)
                return
            except:
                send_message(chat_id, "❌Error al guardar datos. Por favor, intente nuevamente.")
                return

        else:
            send_message(chat_id, "Hola! Escriba /start para solicitar tu permiso de pesca!")
            return



# Главный цикл
def main():
    print("🤖 FSM-бот запущен...")
    while True:
        data = get_notification()
        if data:
            receipt_id = data.get("receiptId")
            body = data.get("body", {})
            sender_data = body.get("senderData", {})
            sender_id = sender_data.get("sender")  # например, 7707XXXXXXX@c.us
            chat_id = sender_data.get("chatId")    # куда отправлять ответ

            message_data = body.get("messageData", {})
            msg_type = message_data.get("typeMessage")

            if msg_type == "textMessage":
                text = message_data.get("textMessageData", {}).get("textMessage")
                if text and sender_id and chat_id:
                    print(f"[{sender_id}] Текст: {text}")
                    handle_message(sender_id, chat_id, "text", text)

            elif msg_type == "imageMessage":
                media_url = message_data.get("fileMessageData", {}).get("downloadUrl")
                if media_url and sender_id and chat_id:
                    print(f"[{sender_id}] Фото: {media_url}")
                    handle_message(sender_id, chat_id, "image", media_url)

            if receipt_id:
                delete_notification(receipt_id)

        time.sleep(DELAY)

if __name__ == "__main__":
    # get_notification()
    main()
# не рабоатет 