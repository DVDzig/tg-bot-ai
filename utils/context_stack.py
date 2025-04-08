async def push_step(state, step: str):
    data = await state.get_data()
    history = data.get("history", [])
    history.append(step)
    await state.update_data(history=history)

async def pop_step(state):
    data = await state.get_data()
    history = data.get("history", [])
    if history:
        last = history.pop()
        await state.update_data(history=history)
        return last
    return None
