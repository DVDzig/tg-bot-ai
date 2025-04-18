from services.sheets import get_user_row_by_id, update_sheet_row


async def reward_referrer(referrer_id: str):
    row = await get_user_row_by_id(referrer_id)
    if not row:
        return

    # Увеличиваем счётчик приглашённых
    current_count = int(row.get("referrals_count", 0))
    new_count = current_count + 1

    # Начисляем 1 бесплатный вопрос
    free_q = int(row.get("free_questions", 0)) + 1

    updates = {
        "referrals_count": new_count,
        "free_questions": free_q
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)


async def set_referrer_if_new(user_id: int, referrer_id: str):
    if str(user_id) == str(referrer_id):
        return  # нельзя быть своим же рефералом

    row = await get_user_row_by_id(user_id)
    if not row:
        return

    if row.get("referrer_id"):
        return  # уже есть пригласивший

    updates = {
        "referrer_id": referrer_id
    }

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)
    await reward_referrer(referrer_id)
