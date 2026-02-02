from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_inline_keyboard(pk):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{pk}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_{pk}")
            ]
        ]
    ) 

def user_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    texts = {
        "ru": ("✅ Всё верно", "❌ Отмена"),
        "uz": ("✅ Hammasi to'g'ri", "❌ Bekor qilish"),
        "en": ("✅ All correct", "❌ Cancel")
    }
    yes_text, no_text = texts.get(lang, texts["ru"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=yes_text, callback_data="user_confirm_yes"),
                InlineKeyboardButton(text=no_text, callback_data="user_confirm_no")
            ]
        ]
    )