import sys
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from aiobot.models.ads import Ads
from aiobot.models.users import Users
from aiobot.texts import TEXTS
from config import CHANNEL_ID

router = Router()

def get_bilingual_condition(condition: str) -> str:
    """Функция для перевода состояния на два языка одновременно"""
    mapping = {
        "Yangi": "НОВОЕ / YANGI",
        "Ideal": "ИДЕАЛЬНОЕ / IDEAL",
        "Yaxshi": "ХОРОШЕЕ / YAXSHI",
        "O'rtacha": "СРЕДНЕЕ / O'RTACHA",
        "Новый": "НОВОЕ / YANGI",
        "Новое": "НОВОЕ / YANGI",
        "Идеальное": "ИДЕАЛЬНОЕ / IDEAL",
        "Хорошее": "ХОРОШЕЕ / YAXSHI",
        "Среднее": "СРЕДНЕЕ / O'RTACHA",
        "Б/у": "Б/У / ISHLATILGAN"
    }
    return mapping.get(condition, condition.upper())

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    
    if not ad:
        return await call.answer("Ad not found")
    
    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"
    formatted_price = f"{int(ad.price):,}".replace(",", " ")

    # Состояние на двух языках
    bil_condition = get_bilingual_condition(ad.condition)

    # ФОРМИРУЕМ ТЕКСТ СТРОГО ПО ВАШЕМУ ПРИМЕРУ (Жирный текст, без эмодзи)
    desc_channel = (
        f"<b>Новое объявление:</b>\n\n"
        f"<b>Название:</b> <b>{ad.title}</b>\n\n"
        f"<b>Цена:</b> <b>{formatted_price} UZS</b>\n\n"
    )

    # Добавляем размер, если он указан
    if ad.size and ad.size != "---":
        desc_channel += f"<b>Размер:</b> <b>{ad.size}</b>\n\n"

    desc_channel += (
        f"<b>Состояние:</b> <b>{bil_condition}</b>\n\n"
        f"<b>Чтобы купить нажмите кнопку ниже.</b>"
    )

    # Кнопка Купить
    buy_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Купить", url="https://t.me/buyursin_admin")]
        ]
    )

    photos = ad.photos.split(",") if ad.photos else []

    try:
        if photos:
            media = []
            for pid in photos:
                media.append(InputMediaPhoto(media=pid))
            
            # Сначала отправляем альбом с фото
            await call.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            
            # Затем отправляем текст с кнопкой (так как в альбомах кнопки не работают)
            await call.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=desc_channel, 
                reply_markup=buy_kb, 
                parse_mode="HTML"
            )
        else:
            await call.bot.send_message(
                chat_id=CHANNEL_ID, 
                text=desc_channel, 
                reply_markup=buy_kb, 
                parse_mode="HTML"
            )
        
        await Ads.update_status(pk, "approved")
        await call.message.edit_reply_markup(reply_markup=None)
        
        # Уведомление пользователю
        success_msg = {"ru": "Объявление опубликовано!", "uz": "E'lon chop etildi!", "en": "Ad published!"}
        await call.bot.send_message(ad.user_id, success_msg.get(lang, success_msg["ru"]))
        await call.answer("Опубликовано!")

    except Exception as e:
        await call.answer(f"Ошибка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    if not ad: return await call.answer("Not found")

    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"

    await Ads.update_status(pk, "rejected")
    
    try:
        await call.message.edit_text(text=f"<b>ОТКЛОНЕНО</b>\n\n{call.message.text}", parse_mode="HTML")
    except: pass

    fail_msg = {"ru": "Объявление отклонено.", "uz": "E'lon rad etildi.", "en": "Ad rejected."}
    await call.bot.send_message(ad.user_id, fail_msg.get(lang, fail_msg["ru"]))
    await call.answer("Отклонено")
