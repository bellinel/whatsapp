import httpx
import time
from engine import session, User

# Конфигурация
GREEN_API_ID ="7105259866"
GREEN_API_TOKEN = '2e3c9fbb79db4f8da8fb516fc8c0e5346d44401551cf4e5881'#"2e3c9fbb79db4f8da8fb516fc8c0e5346d44401551cf4e5881"
BASE_URL = f"https://7105.api.greenapi.com/waInstance{GREEN_API_ID}"
DELAY = 2

# FSM состояния
STATE_WAIT_NAME = "wait_name"
STATE_WAIT_PHONE = "wait_phone"
STATE_WAIT_PHOTO_FRONT = "wait_photo_front"
STATE_WAIT_PHOTO_BACK = "wait_photo_back"
STATE_DONE = "done"

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
    if not user_id or not chat_id:
        print("❌ Ошибка: отсутствует user_id или chat_id")
        return

    # Убедимся, что данные и состояние инициализированы
    state = user_states.setdefault(user_id, None)
    data = user_data.setdefault(user_id, {})

    print(f"➡️ [{user_id}] Состояние: {state} | Тип сообщения: {message_type}")

    if message_type == "text":
        text = content.strip()

        if text.lower() == "/show":
            users = session.query(User).all()
            if not users:
                send_message(chat_id, "База пуста.")
                return
            for u in users:
                msg = (
                    f"👤 ФИО: {u.fio}\n"
                    f"📞 Телефон: {u.phone}\n"
                    f"🖼 Фото (лицо): {u.photo_front}\n"
                    f"🖼 Фото (оборот): {u.photo_back}\n"
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
            data["fio"] = text
            user_states[user_id] = STATE_WAIT_PHONE
            send_message(chat_id, "Gracias! Ahora introduce su numero de contacto +34ххххххх")
            return

        elif state == STATE_WAIT_PHONE:
            if not text.replace("+", "").isdigit():
                send_message(chat_id, "Por favor, ingrese un número válido con +34...")
                return
            data["phone"] = text
            user_states[user_id] = STATE_WAIT_PHOTO_FRONT
            send_message(chat_id, "Envíe una foto del anverso del documento (DNI/NIE)")
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
            data["photo_front"] = url
            user_states[user_id] = STATE_WAIT_PHOTO_BACK
            send_message(chat_id, "Recibido! Ahora envíe una foto del reverso del documento (DNI/NIE)")
            return

        elif state == STATE_WAIT_PHOTO_BACK:
            data["photo_back"] = url
            user_states[user_id] = STATE_DONE

            new_user = User(
                chat_id=user_id,
                fio=data.get("fio"),
                phone=data.get("phone"),
                photo_front=data.get("photo_front"),
                photo_back=data.get("photo_back")
            )
            session.merge(new_user)
            session.commit()

            send_message(chat_id, "✅Tu solicitud fue enviada con exito! En breve contactamos con usted!")
            reset_user(user_id)
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