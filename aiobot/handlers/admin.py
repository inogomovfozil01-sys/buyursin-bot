import sys
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiobot.models.ads import Ads
from aiobot.models.users import Users
from aiobot.texts import TEXTS
from config import CHANNEL_ID

router = Router()

def get_bilingual_condition(condition: str) -> str:
    """Перевод состояния на два языка одновременно, как на фото"""
    mapping = {
        "Yangi": "новые/янги",
        "Ideal": "идеальное/ideal",
        "Yaxshi": "хорошее/yaxshi",
        "O'rtacha": "среднее/o'rtacha",
        "Новый": "новые/янги",
        "Новое": "новые/янги",
        "Идеальное": "идеальное/ideal",
        "Хорошее": "хорошее/yaxshi",
        "Среднее": "среднее/o'rtacha",
        "Б/у": "б/у / ishlatilgan"
    }
    return mapping.get(condition, condition.lower())

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    
    if not ad:
        return await call.answer("Ad not found")
    
    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"
    
    # Форматируем цену с точкой (15.000)
    formatted_price = f"{int(ad.price):,}".replace(",", ".")

    # Получаем состояние (новые/янги)
    bil_condition = get_bilingual_condition(ad.condition)

    # СОЗДАЕМ ТЕКСТ ТОЧНО ПО ПРИМЕРУ С ФОТО
    desc_channel = (
        f"<b>{ad.title}</b>\n\n" # Название (и эмодзи если пользователь сам ввел)
        f"<b>Цена/нархи:</b>\n"
        f"<b>всего {formatted_price} сум</b> 🔥‼️\n\n"
        f"<b>Состояние/холати: {bil_condition}</b> ✅\n\n"
    )

    # Если есть размер, добавляем его тоже красиво
    if ad.size and ad.size != "---":
        desc_channel += f"<b>Размер/ольчами: {ad.size}</b> 📏\n\n"

    # Ссылка на админа в конце как на фото
    desc_channel += f"@buyursin_admin <- Для заказа/заказ килиш учун 🫶"

    photos = ad.photos.split(",") if ad.photos else []

    try:
        if photos:
            media = []
            for i, pid in enumerate(photos):
                if i == 0:
                    # Весь текст идет как подпись к первой картинке
                    media.append(InputMediaPhoto(media=pid, caption=desc_channel, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=pid))
            
            await call.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        else:
            await call.bot.send_message(chat_id=CHANNEL_ID, text=desc_channel, parse_mode="HTML")
        
        await Ads.update_status(pk, "approved")
        await call.message.edit_reply_markup(reply_markup=None)
        
        # Уведомление автору
        success_msg = {"ru": "Объявление опубликовано!", "uz": "E'lon chop etildi!"}
        await call.bot.send_message(ad.user_id, success_msg.get(lang, success_msg["ru"]))
        await call.answer("Успешно опубликовано!")

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

    fail_msg = {"ru": "Объявление отклонено.", "uz": "E'lon rad etildi!"}
    await call.bot.send_message(ad.user_id, fail_msg.get(lang, fail_msg["ru"]))
    await call.answer("Отклонено")
