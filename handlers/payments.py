from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
import database.db as db

router = Router()

@router.callback_query(F.data == "buy_vip_stars")
async def process_buy_vip(callback: CallbackQuery):
    # Telegram Stars (XTR)
    prices = [LabeledPrice(label="VIP на 30 дней", amount=100)]
    
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title="VIP-статус",
        description="Активация VIP-статуса на 30 дней. Преимущества: значок, приоритетный показ, безлимитные лайки.",
        payload="vip_30_days",
        provider_token="", # Для Stars токен должен быть пустым
        currency="XTR",
        prices=prices,
        start_parameter="buy_vip"
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    if message.successful_payment.invoice_payload == "vip_30_days":
        await db.activate_vip(message.from_user.id, days=30)
        await message.answer(
            "Оплата прошла успешно! 🎉\n"
            "Ваш VIP-статус активирован на 30 дней. Удачного общения! 💎"
        )
