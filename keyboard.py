from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_service_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="Сервис 1", callback_data="service_1"))
    keyboard.add(InlineKeyboardButton(text="Сервис 2", callback_data="service_2"))
    keyboard.add(InlineKeyboardButton(text="Сервис 3", callback_data="service_3"))
    keyboard.add(InlineKeyboardButton(text="Сервис 4", callback_data="service_4"))
    keyboard.adjust(1)
    return keyboard.as_markup()







