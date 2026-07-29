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
        settings_core.reload_settings()
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


def processManagement(func):
    """Decorator — restricts access to process management commands."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        settings_core.reload_settings()
        if not settings_core.PROCESS_MANAGEMENT:
            await update.message.reply_text("❌ Process management is disabled\\.\nPlease enable `PROCESS_MANAGEMENT` in the \\.env file to use this command\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def typeManagement(func):
    """Decorator — restricts access to type management commands."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        settings_core.reload_settings()
        if not settings_core.TYPE_ENABLED:
            await update.message.reply_text("❌ Type management is disabled\\.\nPlease enable `TYPE_ENABLED` in the \\.env file to use this command\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper


def runCommand(func):
    """Decorator — restricts access to run command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        settings_core.reload_settings()
        if not settings_core.RUN_COMMAND_ENABLED:
            await update.message.reply_text("❌ Run command is disabled\\.\nPlease enable `RUN_COMMAND_ENABLED` in the \\.env file to use this command\\.", parse_mode=ParseMode.MARKDOWN_V2)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper
