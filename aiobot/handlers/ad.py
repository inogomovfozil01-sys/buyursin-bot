import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message, InputMediaPhoto, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hlink
from aiobot.buttons.keyboards.reply import main_keyboard, lang_keyboard, photos_keyboard, condition_keyboard
from aiobot.buttons.keyboards.inline import admin_inline_keyboard, user_confirm_keyboard
from aiobot.models import Ads, Users
from aiobot.texts import TEXTS
from aiobot.states import AdForm, Register
from config import ADMIN_GROUP_ID
from dispatcher.dispatcher import bot
from aiobot.servise.getifromimg import ai_analyze_category

router = Router()
media_groups_cache = {}

# --- ВСПОМОГАТЕЛЬНЫЕ КЛАВИАТУРЫ И ФУНКЦИИ ---

def size_choice_keyboard(lang):
    """Клавиатура выбора: Есть размер или Нет"""
    texts = {
        "ru": ["Есть размер", "Нет размера"],
        "uz": ["O'lcham bor", "O'lcham yo'q"],
        "en": ["Has size", "No size"]
    }
    btns = texts.get(lang, texts["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btns[0]), KeyboardButton(text=btns[1])]],
        resize_keyboard=True
    )

def parse_price(text: str) -> int:
    """Обработка цены: 1.000 -> 1000, 1.5k -> 1500"""
    text = text.lower().strip().replace(" ", "")
    has_k = any(s in text for s in ["k", "к"])
    # Убираем всё кроме цифр, точек и запятых
    clean_number = re.sub(r"[^0-9.,]", "", text)
    
    if has_k:
        # Если есть 'k', точка — это десятичный разделитель (1.5k = 1500)
        clean_number = clean_number.replace(",", ".")
        return int(float(clean_number) * 1000)
    else:
        # Если 'k' нет, точка/запятая — это разделитель тысяч (1.000 = 1000)
        clean_number = clean_number.replace(".", "").replace(",", "")
        return int(clean_number)

# --- ОСНОВНЫЕ ХЕНДЛЕРЫ ---

@router.message(F.text.in_([TEXTS["add_ad"]["ru"], TEXTS["add_ad"]["uz"], TEXTS["add_ad"]["en"]]))
async def add_ad_start(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    if not user:
        await message.answer(TEXTS["welcome"]["ru"], reply_markup=lang_keyboard())
        await state.set_state(Register.language)
        return
    await message.answer(TEXTS["ad_photos"][user.lang], reply_markup=photos_keyboard(user.lang))
    await state.set_state(AdForm.photos)

@router.message(AdForm.photos, F.photo)
async def ad_photos_step(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if message.media_group_id:
        if message.media_group_id not in media_groups_cache:
            media_groups_cache[message.media_group_id] = []
        media_groups_cache[message.media_group_id].append(message.photo[-1].file_id)
        await asyncio.sleep(0.7)
        if message.media_group_id in media_groups_cache:
            ids = media_groups_cache.pop(message.media_group_id)
            for p_id in ids:
                if len(photos) < 10: photos.append(p_id)
            await state.update_data(photos=photos)
            await message.answer(f"✅ Фото добавлено ({len(photos)}/10).")
    else:
        if len(photos) < 10:
            photos.append(message.photo[-1].file_id)
            await state.update_data(photos=photos)
            await message.answer(f"✅ Фото добавлено ({len(photos)}/10).")

@router.message(AdForm.photos, F.text)
async def photos_ready(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    if message.text.strip() == TEXTS["photos_done"].get(lang, "Готово"):
        data = await state.get_data()
        photos = data.get("photos", [])
        if not photos: return await message.answer("❌ " + TEXTS["ad_photos"][lang])
        
        predicted = await ai_analyze_category(photos[0], message.bot, "Одежда, Обувь, Аксессуары")
        await state.update_data(size_category=predicted if predicted in ["Одежда", "Обувь", "Аксессуары"] else "Одежда")
        await message.answer(TEXTS["ad_price"][lang], reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdForm.price)

@router.message(AdForm.price, F.text)
async def ad_price_step(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    try:
        price = parse_price(message.text)
        await state.update_data(price=price)
        await message.answer(TEXTS["ad_title"][user.lang])
        await state.set_state(AdForm.title)
    except:
        await message.answer("❌ Введите цену цифрами.")

@router.message(AdForm.title, F.text)
async def ad_title_step(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    user = await Users.get(user_id=message.from_user.id)
    await message.answer("📏 Укажите наличие размера:", reply_markup=size_choice_keyboard(user.lang))
    await state.set_state(AdForm.size)

@router.message(AdForm.size, F.text)
async def ad_size_choice_logic(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    text = message.text
    
    # Списки текстов кнопок
    yes_btns = ["Есть размер", "O'lcham bor", "Has size"]
    no_btns = ["Нет размера", "O'lcham yo'q", "No size"]

    if text in yes_btns:
        await message.answer("📝 Введите размер (например: XL, 42 или 27.5):", reply_markup=ReplyKeyboardRemove())
        await state.update_data(waiting_size_text=True)
    elif text in no_btns:
        await state.update_data(size=None) # Размера не будет
        await message.answer(TEXTS["ad_condition"][lang], reply_markup=condition_keyboard(lang))
        await state.set_state(AdForm.condition)
    else:
        # Если пользователь вводит сам текст размера
        data = await state.get_data()
        if data.get("waiting_size_text"):
            await state.update_data(size=text, waiting_size_text=False)
            await message.answer(TEXTS["ad_condition"][lang], reply_markup=condition_keyboard(lang))
            await state.set_state(AdForm.condition)
        else:
            await message.answer("Пожалуйста, используйте кнопки.")

@router.message(AdForm.condition, F.text)
async def ad_condition_step(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    # Записываем состояние и пропускаем дефекты (сразу ставим "Нет")
    await state.update_data(condition=message.text.strip(), defect="Нет")
    data = await state.get_data()

    formatted_price = f"{int(data.get('price', 0)):,}".replace(",", " ")
    
    # Проверка: есть ли размер для отображения
    size_val = data.get('size')
    size_line = f"📏 {TEXTS['field_size'][lang]}: {size_val}\n" if size_val else ""

    ad_text = (
        f"{TEXTS['confirm_header'][lang]}\n\n"
        f"📌 {TEXTS['field_title'][lang]}: {data.get('title', '---')}\n"
        f"💰 {TEXTS['field_price'][lang]}: {formatted_price} UZS\n"
        f"{size_line}"
        f"⚡ {TEXTS['field_condition'][lang]}: {data.get('condition', '---')}\n"
    )
    
    photos = data.get("photos", [])
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=ad_text, parse_mode="Markdown")]
        for p_id in photos[1:]: media.append(InputMediaPhoto(media=p_id))
        await message.answer_media_group(media=media)
    else:
        await message.answer(ad_text, parse_mode="Markdown")
    
    await message.answer(TEXTS["confirm_msg"][lang], reply_markup=user_confirm_keyboard(lang))
    await state.set_state(AdForm.confirm)

@router.callback_query(AdForm.confirm, F.data == "user_confirm_yes")
async def ad_confirm_and_save(callback: CallbackQuery, state: FSMContext):
    user = await Users.get(user_id=callback.from_user.id)
    data = await state.get_data()
    try:
        new_ad = await Ads.create(
            user_id=callback.from_user.id,
            title=data['title'],
            price=float(data['price']),
            size=data.get('size') or "---", # В базу пишем прочерк если пусто
            condition=data['condition'],
            photos=",".join(data.get("photos", [])),
            category=data.get('size_category'),
            defect_info="Нет",
            status='pending'
        )
        try: await callback.message.delete()
        except: pass
        await callback.message.answer("✅ Отправлено на модерацию!", reply_markup=main_keyboard(user.lang))
        await send_to_admin_group(new_ad, user, data)
        await state.clear()
    except Exception as e:
        print(f"Ошибка сохранения: {e}")
        await callback.answer("❌ Ошибка при сохранении.")
    await callback.answer()

async def send_to_admin_group(ad, user, data):
    formatted_price = f"{int(ad.price):,}".replace(",", " ")
    # Получаем телефон из модели Users (поле phone_number)
    user_phone = getattr(user, 'phone_number', 'Нет номера')
    
    # Размер для админа: если его нет, строка не создается
    size_line = f"📏 Размер: {ad.size}\n" if ad.size and ad.size != "---" else ""

    admin_text = (
        f"🆕 <b>ОБЪЯВЛЕНИЕ #{ad.pk}</b>\n\n"
        f"👤 От: {hlink(user.full_name, f'tg://user?id={user.user_id}')} (<code>{user_phone}</code>)\n"
        f"📌 Категория: {ad.category}\n"
        f"🏷 Название: {ad.title}\n"
        f"💰 Цена: {formatted_price} UZS\n"
        f"{size_line}"
        f"⚡ Состояние: {ad.condition}\n"
    )
    
    photos = data.get("photos", [])
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=admin_text, parse_mode="HTML")]
        for p_id in photos[1:]: media.append(InputMediaPhoto(media=p_id))
        await bot.send_media_group(chat_id=ADMIN_GROUP_ID, media=media)
        await bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"Управление #{ad.pk}:", reply_markup=admin_inline_keyboard(ad.pk))
    else:
        await bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text, parse_mode="HTML", reply_markup=admin_inline_keyboard(ad.pk))

@router.callback_query(AdForm.confirm, F.data == "user_confirm_no")
async def ad_cancel(callback: CallbackQuery, state: FSMContext):
    user = await Users.get(user_id=callback.from_user.id)
    try: await callback.message.delete()
    except: pass
    await callback.message.answer("❌ Отменено", reply_markup=main_keyboard(user.lang))
    await state.clear()
    await callback.answer()
