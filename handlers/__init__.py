from aiogram import Dispatcher

from handlers import (
    start_handler,
    info_handler,
    profile_handler,
    shop_handler,
    shop_questions_handler,
    shop_subscription_handler,
    leaderboard_handler,
    missions_handler,
    admin_handler,
    common_navigation
)

def register_all_routers(dp: Dispatcher) -> None:
    dp.include_router(start_handler.router)
    dp.include_router(info_handler.router)
    dp.include_router(profile_handler.router)
    dp.include_router(shop_handler.router)
    dp.include_router(shop_questions_handler.router)
    dp.include_router(shop_subscription_handler.router)
    dp.include_router(leaderboard_handler.router)
    dp.include_router(missions_handler.router)
    dp.include_router(admin_handler.router)
    dp.include_router(common_navigation.router)
