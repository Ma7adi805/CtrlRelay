##-----Libraries-----##
import asyncio, os, time, sys
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, Application
from telegram.constants import ParseMode
from telegram.error import InvalidToken, NetworkError, TelegramError
from core.auth import restricted
from bot_utils.logger import logger
from core.settings import setup_env, reload_settings
from core import settings as settings_module
import configs.launch.add_launch_shortcuts as launch_shortcuts
import handlers, importlib, pkgutil
import modules.audio as audio_module
from modules import files as files_module
import tray as CtrlTray
from tray import Status, Action
import threading

#-----Setup-----##

_bot_loop = None
_bot_thread = None
_app_instance = None

"""
def setup_handlers(app: Application):
    #\"""Set up all command handlers for the bot.\"""
    for _, module_name, _ in pkgutil.walk_packages(handlers.__path__, prefix="handlers."):
        module = importlib.import_module(module_name)
        if hasattr(module, "setup") and callable(module.setup):
            logger.info(f"Running {module_name}.setup()")
            module.setup(app)"""

def setup_handlers(app: Application):
    """Set up all command handlers for the bot (PyInstaller-compatible)."""
    logger.info("Scanning for command handlers...")

    # pkgutil.iter_modules works with PyInstaller's frozen PYZ archive
    for _, module_name, is_pkg in pkgutil.iter_modules(handlers.__path__, prefix=f"{handlers.__name__}."):
        logger.info(f"Discovered module: {module_name}")
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "setup") and callable(module.setup):
                logger.info(f"Running {module_name}.setup()")
                module.setup(app)
            else:
                logger.warning(f"Module {module_name} has no callable setup() function.")
        except Exception as e:
            logger.error(f"Failed to import or setup {module_name}: {e}")          


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"This is your chat ID: *{chat_id}*\n\nPlease add this ID to the ALLOWED\\_CHAT\\_IDS in the \\.env file to allow access\\.", parse_mode=ParseMode.MARKDOWN_V2)


async def build_application():
    reload_settings()
    if not await check_token(settings_module.BOT_TOKEN):
        logger.error("Invalid bot token., please check your .env configuration and restart the application.")
        return None
    app = ApplicationBuilder().token(settings_module.BOT_TOKEN).post_init(on_ready).build()
    setup_handlers(app)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(onButtonClick))
    app.add_error_handler(error_handler)
    return app

def _run_bot_event_loop():
    global _bot_loop, _app_instance
    _bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bot_loop)

    async def runner():
        global _app_instance
        _app_instance = await build_application()
        if _app_instance is None:
            return
        await _app_instance.initialize()
        await _app_instance.start()
        await _app_instance.updater.start_polling()

    _bot_loop.run_until_complete(runner())
    _bot_loop.run_forever()


async def _stop_bot_async():
    global _app_instance
    if _app_instance and _app_instance.updater and _app_instance.updater.running:
        await _app_instance.updater.stop()
        await _app_instance.stop()
        await _app_instance.shutdown()

def stop_bot_sync():
    global _bot_loop, _bot_thread, _app_instance
    if _bot_loop and _bot_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_stop_bot_async(), _bot_loop)
        future.result(timeout=10)
        _bot_loop.call_soon_threadsafe(_bot_loop.stop)
    
    if _bot_thread and _bot_thread.is_alive():
        _bot_thread.join(timeout=5)

    _app_instance = None
    _bot_loop = None
    _bot_thread = None
    CtrlTray.update_status(Status.STOPPED)

def start_bot_sync():
    global _bot_thread
    if _bot_thread is not None and _bot_thread.is_alive():
        return
    if not settings_module.BOT_TOKEN or settings_module.BOT_TOKEN.strip().lower() in ("your_telegram_bot_token_here", ""):
        logger.error("TELEGRAM_TOKEN is missing or not set. Please check your .env configuration.")
        CtrlTray.update_status(Status.ERROR)
        return
    CtrlTray.update_status(Status.STARTING)
    bot_thread = threading.Thread(target=_run_bot_event_loop, name="telegram-poller", daemon=True)
    bot_thread.start()

    # Update status to RUNNING once the thread has launched
    CtrlTray.update_status(Status.RUNNING)
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
            shortcut_path = shortcut_path.replace(os.path.expanduser("~"),"%USERPROFILE%")
            full_path, is_valid = files_module.uncrop_file_path(shortcut_path)
            full_path = full_path.replace("%USERPROFILE%", os.path.expanduser("~"))
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
    else:
        logger.error(f"Bot failed startup validation status: {status}")
        CtrlTray.update_status(Status.ERROR)

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

_bot_running_flag = threading.Event()







def _is_bot_running() -> bool:
    return _bot_running_flag.is_set()

@CtrlTray.onPowerEvent
def handle_power_event(action: Action):
    logger.info(f"Power event received: {action.value}")
    reload_settings()

    if action == Action.START:
        start_bot_sync()

    elif action == Action.STOP:
        logger.info("Stopping bot...")
        CtrlTray.update_status(Status.STOPPING)
        stop_bot_sync()
        logger.info("Bot stopped.")

    elif action == Action.RESTART:
        logger.info("Restarting bot...")
        CtrlTray.update_status(Status.STOPPING)
        stop_bot_sync()
        time.sleep(1)
        start_bot_sync()
        logger.info("Bot restarted successfully.")

@CtrlTray.onQuit
def handle_quit():
    CtrlTray.update_status(Status.STOPPING)
    logger.info("Quit event received. Stopping bot and exiting...")
    stop_bot_sync()
    CtrlTray._icon.stop()
    sys.exit(0)

def main():
    setup_env()
    if not settings_module.BOT_TOKEN or settings_module.BOT_TOKEN.strip().lower() in ("your_telegram_bot_token_here", ""):
        logger.error("TELEGRAM_TOKEN is missing or not set.")
        CtrlTray.update_status(Status.ERROR)
    else:
        start_bot_sync()
    CtrlTray.run()


if __name__ == "__main__":
    main()


#todo: fix InvalidToken bug
"""
[2026-09-02 15:14:40] [INFO] Created default .env file. Please configure it before running the bot.
[2026-09-02 15:14:40] [ERROR] TELEGRAM_TOKEN is missing or not set.
"""







