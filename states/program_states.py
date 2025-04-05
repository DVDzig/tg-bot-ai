from aiogram.fsm.state import StatesGroup, State

class ProgramSelection(StatesGroup):
    level = State()
    program = State()
    module = State()
    discipline = State()
    asking = State()
