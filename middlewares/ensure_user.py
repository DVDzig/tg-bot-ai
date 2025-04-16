from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union
from services.user_service import get_or_create_user, get_user_row_by_id
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import pytz
from keyboards.main_menu import get_main_menu_keyboard

class EnsureUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        user = event.from_user
        if user:
            await get_or_create_user(user)
            data["event_from_user"] = user  # ✅ добавляем в data

            row = await get_user_row_by_id(user.id)
            if row:
                last_str = row.get("last_interaction")
                if last_str:
                    try:
                        last_time = datetime.strptime(last_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone("Europe/Moscow"))
                        now = datetime.now(pytz.timezone("Europe/Moscow"))

                        if now - last_time > timedelta(minutes=15):
                            state: FSMContext = data.get("state")
                            if state:
                                current_state = await state.get_state()

                                if current_state is None or current_state.startswith("Start"):
                                    await state.clear()
                                    await event.answer("👋 Рады видеть тебя снова! Вернёмся в главное меню", reply_markup=get_main_menu_keyboard(user.id))

                    except Exception as e:
                        print(f"[Middleware TimeParse Error] {e}")

        return await handler(event, data)