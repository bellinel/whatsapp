import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from engine import add_admin, assign_service_to_user, get_user_without_service, get_admin
from keyboard import get_service_keyboard
from aiogram.types import InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


PASSWORD = "223323"

bot = Bot(token="7908935966:AAF6YdOiTOne20QL_kNs-6MWIoFRECAQbEU")

dp = Dispatcher()


class Password(StatesGroup):
    password = State()


@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    admin = get_admin(message.from_user.id)
    if admin:
        await message.answer("Выберите сервис", reply_markup=get_service_keyboard())
    else:
        await state.set_state(Password.password)
        await message.answer("Введите пароль")
        
@dp.message(Password.password)
async def password_command(message: types.Message, state: FSMContext):
    if message.text == PASSWORD:
        add_admin(message.from_user.id)
        await state.clear()
        await message.answer("Выберите сервис", reply_markup=get_service_keyboard())
    else:
        await message.answer("Неверный пароль")


@dp.callback_query(lambda c: c.data in ["service_1", "service_2", "service_3", "service_4"])
async def service_1_callback(callback: types.CallbackQuery):
    if callback.data == "service_1":
        service = "сервис 1"
    elif callback.data == "service_2":
        service = "сервис 2"
    elif callback.data == "service_3":
        service = "сервис 3"
    elif callback.data == "service_4":
        service = "сервис 4"
    await callback.message.edit_text(f"Вы выбрали {service}")
    user = get_user_without_service(service)
    if user:
            
            fio = user.fio
            phone = user.phone
            photo_front = user.photo_front
            photo_back = user.photo_back
            region = user.region
            license_type = user.license_type
            urls = [photo_front, photo_back]
            media = [InputMediaPhoto(media=url) for url in urls]
            await callback.message.answer_media_group(media=media)
            await callback.message.answer(f"ФИО: {fio}\nТелефон: {phone}\nРегион: {region}\nТип лицензии: {license_type}")
            
            
            assign_service_to_user(user, service)
            
            await asyncio.sleep(3)
            await callback.message.answer("Выберите сервис", reply_markup=get_service_keyboard())
    else:
        await callback.message.answer("Пользователей нет")
        await asyncio.sleep(3)
        await callback.message.answer("Выберите сервис", reply_markup=get_service_keyboard())
    
    
async def main():
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())







