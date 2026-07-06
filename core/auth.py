from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import core.settings as settings_core
from utils.logger import logger
from telegram.constants import ParseMode


def restricted(func):
    """Decorator — blocks any user not in ALLOWED_CHAT_IDS."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        settings_core.reload_settings()  # Call the function instead of reload()
        user = update.effective_user
        chat_id = update.effective_chat.id
 
        if chat_id not in settings_core.ALLOWED_CHAT_IDS:
            logger.warning(f"Unauthorized access attempt by user {user.id} (@{user.username})")
            await update.message.reply_text("⛔ Unauthorized\\.\nYour chat ID is not in the `ALLOWED_CHAT_IDS` list\\. Please add it in the \\.env file to use this command\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
 
        return await func(update, context, *args, **kwargs)
    return wrapper

def power(func):
    """Decorator — restricts access to power management commands."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        settings_core.reload_settings()
        if not settings_core.POWER_MANAGEMENT:
            await update.message.reply_text("❌ Power management is disabled\\.\nPlease enable `POWER_MANAGEMENT` in the \\.env file to use this command\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

 