import sys
from aiogram import Router, F, html
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiobot.models.ads import Ads
from aiobot.models.users import Users
from aiobot.texts import TEXTS
from config import CHANNEL_ID

router = Router()

@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    
    if not ad:
        return await call.answer("Ad not found")
    
    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"
    formatted_price = f"{int(ad.price):,}".replace(",", " ")

    desc_channel = (
        f"<b>{html.quote(ad.title)}</b>\n\n"
        f"⚡️ {TEXTS['field_condition'][lang]}: <b>{ad.condition}</b>\n"
        f"💰 {TEXTS['field_price'][lang]}: <b>{formatted_price} UZS</b>\n"
        f"📏 {TEXTS['field_size'][lang]}: <b>{ad.size}</b>\n"
    )

    if ad.defect_info:
        desc_channel += f"❗ {TEXTS['field_defect'][lang]}: <b>{ad.defect_info}</b>\n"
    
    desc_channel += f"\n👤 <b>Продавец:</b> <a href='tg://user?id={ad.user_id}'>{html.quote(user.full_name if user else 'User')}</a>"
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
        await call.bot.send_message(ad.user_id, TEXTS["ad_approved"][lang])
        await call.answer("Успешно опубликовано!", show_alert=True)

    except Exception as e:
        await call.answer(f"❌ Ошибка Telegram: {e}\nПроверь, что бот админ в {CHANNEL_ID}", show_alert=True)


@router.callback_query(F.data.startswith("reject_"))
async def reject_ad(call: CallbackQuery):
    pk = int(call.data.split("_")[1])
    ad = await Ads.get(pk)
    if not ad:
        await call.answer("Not found", show_alert=True)
        return

    user = await Users.get(ad.user_id)
    lang = user.lang if user else "ru"

    await Ads.update_status(pk, "rejected")
    
    try:
        await call.message.edit_text(
            text=f"❌ {call.message.text}\n\n<b>ОТКЛОНЕНО</b>",
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"reject_ad: error editing admin message: {e}")

    await call.bot.send_message(ad.user_id, TEXTS["ad_rejected"][lang])
    await call.answer(TEXTS.get("ad_rejected", {}).get(lang, "Rejected"))