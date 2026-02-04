import re
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, CallbackQuery, ReplyKeyboardRemove
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

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def parse_price(text: str) -> int:
    """Логика обработки цены: 1.000 -> 1000, 1.5k -> 1500"""
    text = text.lower().strip().replace(" ", "")
    
    # Ищем суффиксы тысяч
    has_k = any(s in text for s in ["k", "к"])
    # Убираем все буквы (оставляем цифры, точки и запятые)
    clean_number = re.sub(r"[^0-9.,]", "", text)
    
    if has_k:
        # Если есть 'k', точка/запятая — это десятичный разделитель
        clean_number = clean_number.replace(",", ".")
        return int(float(clean_number) * 1000)
    else:
        # Если 'k' нет, то 1.000 или 1,000 — это просто 1000
        clean_number = clean_number.replace(".", "").replace(",", "")
        return int(clean_number)

# --- ХЕНДЛЕРЫ ---

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
            await message.answer(f"✅ Фото добавлено. Всего: {len(photos)}/10. Нажмите 'Готово'.")
    else:
        if len(photos) < 10:
            photos.append(message.photo[-1].file_id)
            await state.update_data(photos=photos)
            await message.answer(f"✅ Фото добавлено ({len(photos)}/10).")
        else:
            await message.answer("❌ Максимум 10 фото.")


@router.message(AdForm.photos, F.text)
async def photos_ready(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    done_text = TEXTS["photos_done"].get(lang, "Готово")
    
    if message.text.strip() == done_text:
        data = await state.get_data()
        photos = data.get("photos", [])
        if not photos:
            return await message.answer("❌ " + TEXTS["ad_photos"][lang])
        
        predicted = await ai_analyze_category(photos[0], message.bot, "Одежда, Обувь, Аксессуары")
        if predicted not in ["Одежда", "Обувь", "Аксессуары"]:
            predicted = "Одежда"

        await state.update_data(size_category=predicted)
        await message.answer(TEXTS["ad_price"][lang], reply_markup=ReplyKeyboardRemove())
        await state.set_state(AdForm.price)


@router.message(AdForm.price, F.text)
async def ad_price_step(message: Message, state: FSMContext):
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    
    try:
        price = parse_price(message.text)
        await state.update_data(price=price)
        await message.answer(TEXTS["ad_title"][lang])
        await state.set_state(AdForm.title)
    except Exception:
        error_price = {
            "ru": "❌ Неверный формат. Используйте только цифры.",
            "uz": "❌ Noto'g'ri format. Faqat raqamlardan foydalaning.",
            "en": "❌ Invalid format. Use numbers only."
        }
        await message.answer(error_price[lang])


@router.message(AdForm.title, F.text)
async def ad_title_step(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    user = await Users.get(user_id=message.from_user.id)
    await message.answer(TEXTS["ad_size"][user.lang], reply_markup=ReplyKeyboardRemove())
    await state.set_state(AdForm.size)


@router.message(AdForm.size, F.text)
async def ad_size_step(message: Message, state: FSMContext):
    await state.update_data(size=message.text)
    user = await Users.get(user_id=message.from_user.id)
    await message.answer(TEXTS["ad_condition"][user.lang], reply_markup=condition_keyboard(user.lang))
    await state.set_state(AdForm.condition)


@router.message(AdForm.condition, F.text)
async def ad_condition_step(message: Message, state: FSMContext):
    """ПРОПУСКАЕМ ДЕФЕКТЫ И ПЕРЕХОДИМ СРАЗУ К ПОДТВЕРЖДЕНИЮ"""
    user = await Users.get(user_id=message.from_user.id)
    lang = user.lang
    
    await state.update_data(condition=message.text.strip(), defect="Нет")
    data = await state.get_data()

    formatted_price = f"{int(data.get('price', 0)):,}".replace(",", " ")
    ad_text = (
        f"{TEXTS['confirm_header'][lang]}\n\n"
        f"📌 {TEXTS['field_title'][lang]}: {data.get('title', '---')}\n"
        f"💰 {TEXTS['field_price'][lang]}: {formatted_price} UZS\n"
        f"📏 {TEXTS['field_size'][lang]}: {data.get('size', '---')}\n"
        f"⚡ {TEXTS['field_condition'][lang]}: {data.get('condition', '---')}\n"
    )

    photos = data.get("photos", [])
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=ad_text, parse_mode="Markdown")]
        for photo_id in photos[1:]:
            media.append(InputMediaPhoto(media=photo_id))
        await message.answer_media_group(media=media)
    else:
        await message.answer(ad_text, parse_mode="Markdown")

    await message.answer(TEXTS["confirm_msg"][lang], reply_markup=user_confirm_keyboard(lang))
    await state.set_state(AdForm.confirm)


@router.callback_query(AdForm.confirm, F.data == "user_confirm_yes")
async def ad_confirm_and_save(callback: CallbackQuery, state: FSMContext):
    user = await Users.get(user_id=callback.from_user.id)
    data = await state.get_data()
    photo_str = ",".join(data.get("photos", []))
    
    try:
        new_ad = await Ads.create(
            user_id=callback.from_user.id,
            title=data['title'],
            price=float(data['price']),
            size=data['size'],
            condition=data['condition'],
            photos=photo_str,
            category=data.get('size_category'),
            defect_info=data.get('defect'),
            status='pending'
        )

        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer("✅ Отправлено на модерацию!", reply_markup=main_keyboard(user.lang))
        await send_to_admin_group(new_ad, user, data)
        await state.clear()
        
    except Exception as e:
        await callback.answer("❌ Ошибка при сохранении.", show_alert=True)
    
    await callback.answer()


async def send_to_admin_group(ad, user, data):
    formatted_price = f"{int(ad.price):,}".replace(",", " ")
    admin_text = (
        f"🆕 <b>ОБЪЯВЛЕНИЕ #{ad.pk}</b>\n\n"
        f"👤 От: {hlink(user.full_name, f'tg://user?id={user.user_id}')}\n"
        f"📌 Категория: {ad.category}\n"
        f"🏷 Название: {ad.title}\n"
        f"💰 Цена: {formatted_price} UZS\n"
        f"📏 Размер: {ad.size}\n"
        f"⚡ Состояние: {ad.condition}\n"
    )

    photos = data.get("photos", [])
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=admin_text, parse_mode="HTML")]
        for p_id in photos[1:]:
            media.append(InputMediaPhoto(media=p_id))
        
        await bot.send_media_group(chat_id=ADMIN_GROUP_ID, media=media)
        await bot.send_message(chat_id=ADMIN_GROUP_ID, text=f"Управление #{ad.pk}:", reply_markup=admin_inline_keyboard(ad.pk))
    else:
        await bot.send_message(chat_id=ADMIN_GROUP_ID, text=admin_text, parse_mode="HTML", reply_markup=admin_inline_keyboard(ad.pk))


@router.callback_query(AdForm.confirm, F.data == "user_confirm_no")
async def ad_cancel(callback: CallbackQuery, state: FSMContext):
    user = await Users.get(user_id=callback.from_user.id)
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer("❌ Отменено", reply_markup=main_keyboard(user.lang))
    await state.clear()
    await callback.answer()
