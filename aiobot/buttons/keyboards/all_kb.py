from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="📖 Логин")],
        [KeyboardButton(text="📝 Регистриция")]
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True
    )

    return keyboard

def contact_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text="Отправить контакт", request_contact=True)],
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True,
    )

    return keyboard
