from aiogram.fsm.state import StatesGroup, State


class GrantSubscription(StatesGroup):
    waiting_for_user_id = State()
    plan_type = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()
