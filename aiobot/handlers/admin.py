import sys
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiobot.models.ads import Ads
from aiobot.models.users import Users
from aiobot.texts import TEXTS
from config import CHANNEL_ID

router = Router()

def get_bilingual_condition(condition: str) -> str:
    """
    Распознает кнопки со скриншота и выдает двуязычный текст.
    """
    c = condition.lower()
    
    # 🆕 Новый
    if "новый" in c and "почти" not in c:
        return "новое/yangi"
    
    # ✨ Почти новый
    if "почти новый" in c or "ideal" in c:
        return "идеальное/ideal"
    
    # 👍 Хорошее
    if "хорошее" in c or "yaxshi" in c:
        return "хорошее/yaxshi"
    
    # 👌 Среднее
    if "среднее" in c or "o'rtacha" in c:
        return "среднее/o'rtacha"
    
    # 🔧 Требует ремонта
    if "ремонта" in c or "ta'mir" in c:
        return "требует ремонта/ta'mirga muhtoj"
        
    return html.quote(condition.lower())

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    
    if not ad:
        return await call.answer("Ad not found")
    
    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"
    
    # Форматируем цену: 150.000
    formatted_price = f"{int(ad.price):,}".replace(",", ".")

    # Состояние на двух языках
    bil_condition = get_bilingual_condition(ad.condition)
    
    # Экранируем данные пользователя для безопасности HTML
    safe_title = html.quote(ad.title)

    # СОЗДАЕМ ТЕКСТ ТОЧНО ПО ПРИМЕРУ (как на фото Гарри Поттера)
    desc_channel = (
        f"<b>{safe_title}</b>\n\n"
        f"<b>Цена/нархи:</b>\n"
        f"<b>всего {formatted_price} сум</b> 🔥‼️\n\n"
        f"<b>Состояние/холати: {bil_condition}</b> ✅\n\n"
    )

    # Размер добавляем если он есть
    if ad.size and ad.size != "---":
        safe_size = html.quote(ad.size)
        desc_channel += f"<b>Размер/ольчами: {safe_size}</b> 📏\n\n"

    # Ссылка на админа (используем тире для безопасности парсинга)
    desc_channel += f"@buyursin_admin — Для заказа/заказ килиш учун 🫶"

    photos = ad.photos.split(",") if ad.photos else []

    try:
        if photos:
            media = []
            for i, pid in enumerate(photos):
                if i == 0:
                    media.append(InputMediaPhoto(media=pid, caption=desc_channel, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(media=pid))
            
            await call.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        else:
            await call.bot.send_message(chat_id=CHANNEL_ID, text=desc_channel, parse_mode="HTML")
        
        await Ads.update_status(pk, "approved")
        await call.message.edit_reply_markup(reply_markup=None)
        
        # Уведомление пользователю
        success_msg = {"ru": "Объявление опубликовано!", "uz": "E'lon chop etildi!"}
        await call.bot.send_message(ad.user_id, success_msg.get(lang, success_msg["ru"]))
        await call.answer("Успешно опубликовано!")

    except Exception as e:
        await call.answer(f"Ошибка: {str(e)}", show_alert=True)


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
