from datetime import datetime
import logging
import os
import requests
import hashlib
import hmac
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    PreCheckoutQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from localizations import localizations
from boosters import buy_boosters, BOOSTERS, process_booster_purchase
from config import (
    TG_TOKEN, 
    TMA_URL, 
    API_URL, 
    COMMUNITY_LINK,
    CHAT_EN_LINK,
    CHAT_RU_LINK,
    SITE_LINK,
    PRODUCTION,
    IS_RC,
    AUTHORIZED_USERS
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WELCOME_VIDEO_ID = 'intro.mp4'

async def start(update: Update, context):
    """Handle /start command and display main menu"""
    user_id = update.message.from_user.id
    
    # Check authorization for non-production/RC environment
    if (not PRODUCTION or IS_RC) and user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("🔐 Access denied!")
        return

    # Get user language and localization
    user_lang = update.effective_user.language_code[:2]
    lang_data = localizations.get(user_lang, localizations['en'])

    # Create main menu keyboard
    keyboard = [
        [InlineKeyboardButton(lang_data['play_button'], web_app={"url": TMA_URL})],
        [InlineKeyboardButton("🔋 Buy boosters", callback_data='buy_aeon')],
        [InlineKeyboardButton(lang_data['join_community'], url=COMMUNITY_LINK)],
        [
            InlineKeyboardButton(lang_data['chat_en'], url=CHAT_EN_LINK),
            InlineKeyboardButton(lang_data['chat_ru'], url=CHAT_RU_LINK)
        ],
        [InlineKeyboardButton(lang_data['site'], url=SITE_LINK)],
        [InlineKeyboardButton(lang_data['game_guide_button'], callback_data='faq')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send welcome video with menu
    await update.message.reply_video(
        video=open(WELCOME_VIDEO_ID, 'rb'),
        caption=lang_data['welcome_message'],
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def button_callback(update: Update, context):
    """Handle button clicks from inline keyboards"""
    query = update.callback_query
    await query.answer()

    user_lang = update.effective_user.language_code[:2]
    lang_data = localizations.get(user_lang, localizations['en'])

    if query.data == 'faq':
        await query.message.reply_markdown_v2(
            text=lang_data['game_guide_message'],
            disable_web_page_preview=True
        )
    elif query.data.startswith('boost_'):
        booster_amount = query.data.split('_')[1]
        await process_booster_purchase(update, booster_amount)
    elif query.data == 'buy_aeon':
        await buy_boosters(update, context, message_func=query.message.reply_text)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Telegram payment precheckout"""
    query = update.pre_checkout_query
    is_pending = await is_invoice_pending(invoice_id=query.invoice_payload)

    await query.answer(
        ok=is_pending,
        error_message="Payment declined. Please try again." if not is_pending else None
    )

async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle successful payments"""
    invoice_id = update.message.successful_payment.invoice_payload
    is_purchase_valid = await validate_purchase(invoice_id)
    logger.info(f"Purchase with invoice id: {invoice_id} validated with result: {is_purchase_valid}")

async def all_messages_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all other messages including refunds"""
    if update.message.refunded_payment:
        invoice_id = update.message.refunded_payment.invoice_payload
        is_purchase_refunded = await refund_purchase(invoice_id)
        logger.info(f"Purchase {invoice_id} refunded with result: {is_purchase_refunded}")

async def is_invoice_pending(invoice_id: str) -> bool:
    """Check if invoice is in pending state"""
    try:
        url = f"{API_URL}invoices/{invoice_id}"
        response = requests.get(url)
        return response.status_code == 200 and response.json().get('status') == 'pending'
    except Exception as e:
        logger.error(f"Error checking invoice status: {e}")
        return False

async def validate_purchase(invoice_id: str) -> bool:
    """Validate purchase completion"""
    checksum = await hash_message(invoice_id)
    body = json.dumps({"checksum": checksum})
    try:
        response = requests.post(API_URL + f"invoices/{invoice_id}/validate", body)
        return response.status_code == 200 and response.json().get('is_validated')
    except Exception as e:
        logger.error(f"Error validating purchase: {e}")
        return False

async def refund_purchase(invoice_id: str) -> bool:
    """Process purchase refund"""
    checksum = await hash_message(invoice_id)
    body = json.dumps({"checksum": checksum})
    try:
        response = requests.post(API_URL + f"invoices/{invoice_id}/refund", body)
        return response.status_code == 200 and response.json().get('is_refunded')
    except Exception as e:
        logger.error(f"Error processing refund: {e}")
        return False

async def hash_message(message: str) -> str:
    """Generate HMAC SHA256 hash for message"""
    return hmac.new(
        key=TG_TOKEN.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

def main():
    """Initialize and start the bot"""
    application = Application.builder().token(TG_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy_boosters", buy_boosters))
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.ALL, all_messages_callback))

    # Start bot
    application.run_polling()

if __name__ == '__main__':
    main()
