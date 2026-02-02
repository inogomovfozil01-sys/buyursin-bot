from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiobot.buttons.keyboards.reply import main_keyboard, lang_keyboard, phone_keyboard
from aiobot.texts import TEXTS
from aiobot.models.users import Users
from aiogram.filters import Command, StateFilter
import logging

from aiobot.states import Register

router = Router()

LANGS = {"🇷🇺 Русский": "ru", "🇺🇿 O‘zbekcha": "uz", "🇬🇧 English": "en"}


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    logging.info(f"cmd_start: user_id={message.from_user.id}, text={message.text}")

    user = await Users.get(message.from_user.id)
    if user:
        lang = user.lang or "ru"
        await message.answer(TEXTS["start_desc"][lang], reply_markup=main_keyboard(lang))
    else:
        await message.answer(TEXTS["welcome"]["ru"], reply_markup=lang_keyboard())
        await state.set_state(Register.language)


@router.message(Command("lang"))
async def change_lang(message: Message, state: FSMContext):
    await state.clear()
    user = await Users.get(user_id=message.from_user.id)
    logging.info(f"/lang: user_id={message.from_user.id}")
    await message.answer(
        TEXTS["lang_prompt"][user.lang if user.lang else "ru"],
        reply_markup=lang_keyboard()
    )
    await state.set_state(Register.language)


@router.message(StateFilter(Register.language), F.text.in_(LANGS.keys()))
async def register_choose_lang(message: Message, state: FSMContext):
    logging.info(f"register_choose_lang: user_id={message.from_user.id}, text={message.text}")
    lang = LANGS[message.text]
    await state.update_data(lang=lang)

    user = await Users.get(message.from_user.id)
    if user and user.phone_number:
        await Users.update(message.from_user.id, lang=lang)
        await message.answer(TEXTS["start_desc"][lang], reply_markup=main_keyboard(lang))
        await state.clear()
    else:
        await message.answer(TEXTS["ask_phone"][lang], reply_markup=phone_keyboard(lang))
        await state.set_state(Register.phone)


@router.message(StateFilter(Register.language))
async def invalid_language(message: Message, state: FSMContext):
    await message.answer(TEXTS["invalid_lang"]["ru"], reply_markup=lang_keyboard())


@router.message(StateFilter(Register.phone), F.contact)
async def register_phone(message: Message, state: FSMContext):
    logging.info(f"register_phone: user_id={message.from_user.id}, contact={message.contact}")
    data = await state.get_data()
    lang = data.get("lang", "ru")

    if message.contact.user_id != message.from_user.id:
        await message.answer(TEXTS["invalid_contact"][lang], reply_markup=phone_keyboard(lang))
        return

    phone = message.contact.phone_number
    await Users.create(
        user_id=message.from_user.id,
        lang=lang,
        full_name=message.from_user.full_name,
        phone_number=phone
    )
    await message.answer(TEXTS["reg_success"][lang], reply_markup=main_keyboard(lang))
    await state.clear()


@router.message(StateFilter(Register.phone))
async def invalid_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await message.answer(TEXTS["invalid_phone"][lang], reply_markup=phone_keyboard(lang))