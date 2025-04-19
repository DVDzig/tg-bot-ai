from services.sheets import get_user_row_by_id, update_sheet_row
from services.user_service import update_user_plan



async def reward_referrer(referrer_id: str):
    from bot import bot
    row = await get_user_row_by_id(referrer_id)
    if not row:
        return

    current_count = int(row.get("referrals_count", 0)) + 1
    current_free = int(row.get("free_questions", 0))
    current_rewards = row.get("referral_rewards", "")
    awarded = set(map(str.strip, current_rewards.split(","))) if current_rewards else set()

    updates = {
        "referrals_count": current_count,
        "referral_rewards": current_rewards  # обновим ниже
    }

    new_awards = []

    # 🎁 1 приглашённый — +5 бесплатных вопросов
    if current_count >= 1 and "1" not in awarded:
        updates["free_questions"] = current_free + 5
        new_awards.append("1")

    # 🎁 3 приглашённых — подписка Лайт на 3 дня
    if current_count >= 3 and "3" not in awarded:
        await update_user_plan(referrer_id, "lite", 3)
        new_awards.append("3")

    # 🎁 10 приглашённых — NFT Амбассадор
    if current_count >= 10 and "10" not in awarded:
        new_awards.append("10")
        try:
            await bot.send_message(
                chat_id=int(referrer_id),
                text="🎉 Ты стал <b>Амбассадором</b>! Твоя NFT-карточка будет выдана скоро.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[NFT notify error] {e}")

    # 🎁 50+ — подписка Про на 30 дней
    if current_count >= 50 and "50" not in awarded:
        await update_user_plan(referrer_id, "pro", 30)
        new_awards.append("50")

    # Обновляем награды
    updated_rewards = awarded.union(new_awards)
    updates["referral_rewards"] = ",".join(sorted(updated_rewards))

    await update_sheet_row(row.sheet_id, row.sheet_name, row.index, updates)

    if new_awards:
        try:
            await bot.send_message(
                chat_id=int(referrer_id),
                text="🎉 Ты получил(а) новый бонус за приглашения! Проверь свой профиль или раздел с подпиской!",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[Notify error] {e}")
