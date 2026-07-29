##-----Libraries-----##
import asyncio
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, Application
from telegram.constants import ParseMode
from telegram.error import InvalidToken, NetworkError, TelegramError
from core.auth import restricted
from utils.logger import logger
from core.settings import BOT_TOKEN, setup_env
import configs.launch.add_launch_shortcuts as launch_shortcuts
import handlers, importlib, pkgutil
import modules.audio as audio_module
from modules import files as files_module
#-----Setup-----##

def setup_handlers(app:Application):
    """Set up all command handlers for the bot."""
    for _, module_name, _ in pkgutil.walk_packages(handlers.__path__, prefix="handlers."):
        module = importlib.import_module(module_name)
        if hasattr(module, "setup") and callable(module.setup):
            logger.info(f"Running {module_name}.setup()")
            module.setup(app)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"This is your chat ID: *{chat_id}*\n\nPlease add this ID to the ALLOWED\\_CHAT\\_IDS in the \\.env file to allow access\\.", parse_mode=ParseMode.MARKDOWN_V2)





def get_shortcut_id(button_data: str) -> int | str | None:
    """Extract the shortcut ID from the button data."""
    try:
        _, shortcut_id = button_data.split(":", 1)
        if shortcut_id.isdigit():
            return int(shortcut_id)
        else:
            return shortcut_id
    except (ValueError, IndexError):
        logger.error(f"Invalid button data format: {button_data}")
        return None



async def onButtonClick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("launch:"):
        shortcut_id = get_shortcut_id(query.data)
        result = launch_shortcuts.launch_shortcut_by_id(shortcut_id)
        await query.message.reply_text(result[:200])

    elif query.data.startswith("delete:"):
        shortcut_id = get_shortcut_id(query.data)
        result = launch_shortcuts.remove_shortcut_by_id(shortcut_id)
        await query.message.reply_text(result[:200])

    elif query.data.startswith("setaudio:"):
        device_index = get_shortcut_id(query.data)
        devices = audio_module.get_clean_output_devices()
        target = next((d for d in devices if d['original_index'] == device_index), None)
        result = audio_module.set_default_output_device(target['name']) if target else f"❌ Could not find device with index: {device_index}"
        await query.message.reply_text(result[:200])
    elif query.data.startswith("ls:"):
        shortcut_path = get_shortcut_id(query.data)
        if shortcut_path is not None:
            full_path, is_valid = files_module.uncrop_file_path(shortcut_path)
            logger.debug(f"Uncropped path: {full_path}, Valid: {is_valid}, Cropped: {shortcut_path}")
            if is_valid:
                list_contents, error = files_module.list_directory_contents(full_path)
                logger.debug(f"Directory contents of {full_path}: {list_contents}, Error: {error}")
                if error:
                    await query.message.reply_text(f"❌ Error listing directory contents: {error}")
                    return
                if list_contents:
                     contents_str = "\n".join(f"{i+1}. <b>{item}</b>" for i, item in enumerate(list_contents))
                     await query.message.reply_text(f"Contents of <code>{full_path}</code>:\n{contents_str}", parse_mode=ParseMode.HTML)

                else:
                    await query.message.reply_text(f"The directory <code>{full_path}</code> is empty.", parse_mode=ParseMode.HTML)
            else:
                await query.message.reply_text(f"❌ The path '{full_path}' is not allowed. Please check your .env configuration.")
        else:
            await query.message.reply_text("❌ Invalid path provided.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Update caused error", exc_info=context.error)


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Power Commands", callback_data="help_power"), InlineKeyboardButton("Management Commands", callback_data="help_process"), InlineKeyboardButton("Utility Commands", callback_data="help_utility")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a category to view available commands:", reply_markup=reply_markup)


async def validate_bot(application: ApplicationBuilder):
    try:
        me = await application.bot.get_me()
        return "Connected"

    except InvalidToken:
        #logger.error("Invalid bot token.")
        return "Invalid"

    except NetworkError as e:
        #logger.error(f"Network error: {e}")
        return "NetworkError"

    except TelegramError as e:
        #logger.error(f"Telegram API error: {e}")
        return "TelegramError"

async def on_ready(application: Application):
    status = await validate_bot(application)
    if status == "Connected":
        logger.info(f"Bot is ready and running as: {application.bot.username}.")
    elif status == "Invalid":
        logger.error("Bot token is invalid. Please check your .env file.")
    elif status == "NetworkError":
        logger.error("Network error occurred while connecting to Telegram API.")
    elif status == "TelegramError":
        logger.error("An error occurred with the Telegram API.")

async def check_token(token: str) -> bool:
    """Validate token directly with the Telegram API."""
    try:
        async with Bot(token) as bot:
            me = await bot.get_me()
            logger.info(f"Connected successfully as @{me.username}")
            return True
    except InvalidToken:
        logger.error("❌ Invalid bot token provided in environment variables.")
        return False
    except NetworkError as e:
        logger.error(f"❌ Network error while validating token: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to connect: {e}")
        return False




def main():
    setup_env()
    TOKEN = BOT_TOKEN
    if not TOKEN or TOKEN.strip() == "YOUR_TELEGRAM_BOT_TOKEN":
        logger.error("TELEGRAM_TOKEN is missing or not set.")
        return
    
    # 1. Run the token check first
    is_valid = asyncio.run(check_token(TOKEN))
    
    # 2. Stop execution explicitly if validation fails
    if not is_valid:
        logger.error("Aborting startup due to invalid credentials.")
        return

    # 3. Only proceed with application setup if token is verified
    app = ApplicationBuilder().token(TOKEN).post_init(on_ready).build()
    del TOKEN

    setup_handlers(app)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(onButtonClick))
    
    app.add_error_handler(error_handler)

    try:
        logger.info("Starting bot polling...")
        app.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")

if __name__ == "__main__":
    main()