from aiogram import BaseMiddleware, Router
from aiogram.types import Message
from typing import Callable, Awaitable, Dict, Any
from aiobot.models.users import Users


router = Router()


class AuthMiddleware(BaseMiddleware):
    async def __call__(self,
                       handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
                       event: Message,
                       data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id
        user = await Users.get(user_id=user_id)


        if not user:
            await event.answer("❌ Вы не авторизованы. Используйте /start для входа.")
            return
        return await handler(event, data)

router.message.middleware(AuthMiddleware())