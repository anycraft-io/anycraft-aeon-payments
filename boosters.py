import datetime
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from payment import PaymentAPI
import uuid

logger = logging.getLogger(__name__)
payment_api = PaymentAPI()

# Booster packages configuration
BOOSTERS = {
    "5": {
        "price": 100,  # Price in cents
        "amount": 5,
        "callback_data": "boost_5"
    },
    "10": {
        "price": 150,
        "amount": 10,
        "callback_data": "boost_10"
    },
    "20": {
        "price": 200,
        "amount": 20,
        "callback_data": "boost_20"
    },
    "50": {
        "price": 400,
        "amount": 50,
        "callback_data": "boost_50"
    },
    "100": {
        "price": 450,
        "amount": 100,
        "callback_data": "boost_100"
    }
}

async def buy_boosters(update: Update, context: ContextTypes.DEFAULT_TYPE, message_func=None):
    """Display booster purchase menu"""
    user_id = update.effective_user.id
    logger.info(f"Buy boosters command received from user {user_id}")
    
    # Create keyboard with booster options
    keyboard = []
    for booster_key, booster_data in BOOSTERS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"{booster_key}🔋 (${float(booster_data['price']/ 100)})",
                callback_data=booster_data["callback_data"]
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = '''🔋Boosters allow you to refill your crafting energy, so you can keep crafting without waiting. 

Select a pack below to keep the creativity flowing!'''
    
    # Send message based on context
    if message_func is None:
        await update.message.reply_text(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await message_func(
            text=message_text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )

async def process_booster_purchase(update: Update, booster_amount: str):
    """Process booster purchase request"""
    query = update.callback_query
    user_id = update.effective_user.id
    logger.info(f"Processing booster purchase for user {user_id}, amount: {booster_amount}")
    
    # Validate booster amount
    if booster_amount not in BOOSTERS:
        logger.warning(f"Invalid booster amount selected: {booster_amount}")
        await query.message.reply_text("Invalid booster package selected!")
        return
    
    booster = BOOSTERS[booster_amount]
    order_id = f"BOOST_{uuid.uuid4().hex[:12]}_{user_id}"
    
    # Prepare custom data
    custom_data = {
        "type": "booster",
        "amount": str(booster_amount),
        "user_id": user_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    # Create payment order
    payment_result = await payment_api.create_payment(
        amount=booster["price"],
        user_id=user_id,
        order_id=order_id,
        custom_data=custom_data
    )
    
    # Handle payment errors
    if payment_result.get("error", False):
        await query.message.reply_text(
            "Sorry, there was an error processing your payment. Please try again later."
        )
        return
    
    # Get payment URL
    payment_url = payment_result.get("model", {}).get("webUrl")
    if not payment_url:
        await query.message.reply_text(
            "Sorry, there was an error generating payment link. Please try again later."
        )
        return
    
    # Create payment button
    keyboard = [
        [InlineKeyboardButton("[AEON] Please process your purchase", web_app={"url": payment_url})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send payment message
    await query.message.reply_text(
        f"Great choice! You're about to purchase {booster_amount} boosters for ${float(booster['price']/100)}\n"
        "Click the button below to proceed with payment:",
        reply_markup=reply_markup
    )
