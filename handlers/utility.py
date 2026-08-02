import os, pyautogui
from uuid import uuid4
from time import time
from html import escape
from core.auth import restricted, typeManagement, runCommand
import core.settings as settings_core
from core.settings import reload_settings
from bot_utils.logger import logger
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton, Document, PhotoSize
from telegram.ext import CommandHandler, ContextTypes, Application, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from modules import files as files_module
from modules import audio

async def run_shell_command(command: str) -> tuple[str, Exception | None]:
    """Run a shell command and return its output."""
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr
        return output.strip(), None
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}")
        return "", e


@restricted
def list_directory_contents(path: str) -> tuple[list[str], Exception | None]:
    """List the contents of a directory."""
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return [], FileNotFoundError(f"Path does not exist: {path}")
    try:
        return os.listdir(path), None
    except Exception as e:
        logger.error(f"Error listing directory contents for {path}: {e}")
        return [], e
    
def is_path_allowed(path: str) -> bool:
    """Check if the given path is allowed based on settings."""
    reload_settings()
    normalized_path = os.path.abspath(path)
    for allowed_path in settings_core.ALLOWED_PATHS:
        allowed_path = allowed_path.strip().replace("%USERPROFILE%", os.path.expanduser("~"))
        if normalized_path.startswith(os.path.abspath(allowed_path)):
            return True
    logger.warning(f"Access denied for path: {normalized_path}")
    return False

def is_path_allowed_download(path: str) -> bool:
    """Check if the given path is allowed based on settings."""
    reload_settings()
    normalized_path = os.path.abspath(path)
    for allowed_path in settings_core.DOWNLOAD_PATH:
        allowed_path = allowed_path.strip().replace("%USERPROFILE%", os.path.expanduser("~"))
        if normalized_path.startswith(os.path.abspath(allowed_path)):
            return True
    logger.warning(f"Access denied for path: {normalized_path}")
    return False


def upload_file(file_path: str) -> tuple[str, Exception | None]:
    """Upload a file to the server."""
    if not os.path.isfile(file_path):
        logger.error(f"File does not exist: {file_path}")
        return "", FileNotFoundError(f"File does not exist: {file_path}")
    try:
        # Simulate file upload process
        logger.info(f"Uploading file: {file_path}")

        return f"File <code>{file_path}</code> uploaded successfully.", None
    except Exception as e:
        logger.error(f"Error uploading file {file_path}: {e}")
        return "", e

def create_temp_directory() -> str:
    """Create a temporary directory for file operations."""
    folder_name = "TEMP"
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
        logger.info(f"Temporary directory created: {folder_name}")
    else: 
        logger.info(f"Temporary directory already exists: {folder_name}")
    return folder_name

def check_size(doc:Document | PhotoSize) -> bool:
    """Check if the document size is within the allowed limit."""
    reload_settings()
    max_size_bytes = settings_core.MAX_UPLOAD_SIZE * 1024 * 1024
    if doc.file_size > max_size_bytes:
        logger.warning(f"Document size {doc.file_size} exceeds limit of {max_size_bytes} bytes.")
        return False
    return True

ASK_FILE = 1
ASK_FILE_PATH = 2
class utilityCmd:

    def _build_path_keyboard(self, context: ContextTypes.DEFAULT_TYPE):
        keyboard = []
        path_map = context.user_data.setdefault("upload_path_map", {})
        file_token = context.user_data.get("upload_file_token")

        if not file_token:
            return None

        for allowed_path in settings_core.ALLOWED_PATHS:
            allowed_path = allowed_path.strip().replace("%USERPROFILE%", os.path.expanduser("~"))
            if os.path.exists(allowed_path):
                path_token = uuid4().hex[:8]
                path_map[path_token] = allowed_path
                keyboard.append([
                    InlineKeyboardButton(
                        allowed_path,
                        callback_data=f"up:{file_token}:{path_token}"
                    )
                ])
            else:
                logger.warning(f"Allowed path does not exist: {allowed_path}")
        for allowed_path in settings_core.DOWNLOAD_PATH:
            allowed_path = allowed_path.strip().replace("%USERPROFILE%", os.path.expanduser("~"))
            if not os.path.exists(allowed_path):
                logger.warning(f"Download path does not exist: {allowed_path}, Attempting to create it.")
                try:
                    os.makedirs(allowed_path)
                    logger.info(f"Download path created: {allowed_path}")
                except Exception as e:
                    logger.error(f"Error creating download path {allowed_path}: {e}")
                    return None
            try:
                path_token = uuid4().hex[:8]
                path_map[path_token] = allowed_path
                keyboard.append([
                    InlineKeyboardButton(
                        allowed_path,
                        callback_data=f"up:{file_token}:{path_token}"
                    )
                ])
                return InlineKeyboardMarkup(keyboard) if keyboard else None
            except Exception as e:
                logger.error(f"Error adding download path {allowed_path} to keyboard: {e}")
                return None

        return InlineKeyboardMarkup(keyboard) if keyboard else None
    
    async def upload(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /upload command. (Part1)"""
        reload_settings()
        context.user_data.pop("upload_file_token", None)
        context.user_data.pop("uploaded_file_path", None)
        context.user_data.pop("upload_path_map", None)
        logger.debug(f"ALLOWED_PATHS: {settings_core.ALLOWED_PATHS}, DOWNLOAD_PATH: {settings_core.DOWNLOAD_PATH}")
        if settings_core.ALLOWED_PATHS or settings_core.DOWNLOAD_PATH:
            await update.message.reply_text("Please send the file you want to upload.")
            return ASK_FILE
        await update.message.reply_text("File upload is not allowed. No allowed paths are configured.\nPlease add allowed paths in the .env file.") 
        return ConversationHandler.END

    async def upload2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the file upload process. (Part2)"""
        message = update.message
        file = None
        file_name = None
        try:
            if message.document:
                if not check_size(message.document):
                    await message.reply_text(f"File size exceeds the maximum limit of {settings_core.MAX_UPLOAD_SIZE} MB.\nPlease send a smaller file.\nTo cancel, type cancel.")
                    return ASK_FILE
                file = await message.document.get_file()
                
                file_name = message.document.file_name
            elif message.photo:
                # photos arrive as photo, not document
                if not check_size(message.photo[-1]):
                    await message.reply_text(f"Photo size exceeds the maximum limit of {settings_core.MAX_UPLOAD_SIZE} MB.\nPlease send a smaller photo.\nTo cancel, type cancel.")
                    return ASK_FILE
                file = await message.photo[-1].get_file()
                photo_extension = os.path.splitext(os.path.basename(file.file_path))[1].lstrip('.') or 'jpg'
                file_name = f"photo_{int(time())}.{photo_extension}"
            else:
                if message.text and message.text.lower() == "cancel":
                    await message.reply_text("Upload canceled.")
                    return ConversationHandler.END
                await message.reply_text("Please send a file (document or photo).\nTo cancel, type cancel.")
                return ASK_FILE
            logger.info(f"Received file: {file_name}, size: {file.file_size} bytes")
            if file.file_size > settings_core.MAX_UPLOAD_SIZE * 1024 * 1024:
                await message.reply_text(f"File size exceeds the maximum limit of {settings_core.MAX_UPLOAD_SIZE} MB.\nPlease send a smaller file.\nTo cancel, type cancel.")
                return ASK_FILE
        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            await message.reply_text("Could not read that file. Please try again.\nTo cancel, type cancel.")
            return ASK_FILE

        if not file:
            await message.reply_text("No file received. Please send a valid file.\nTo cancel, type cancel.")
            return ASK_FILE
        
        try:
            file_path = os.path.join(create_temp_directory(), os.path.basename(file_name))
            await file.download_to_drive(file_path)
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            await message.reply_text(f"Error downloading file: {e}")
            return ConversationHandler.END

        context.user_data["uploaded_file_path"] = file_path
        context.user_data["upload_file_token"] = uuid4().hex[:8]

        message_, error = upload_file(file_path)
        if error:
            await message.reply_text(f"Error uploading file: {error}")
            return ConversationHandler.END

        reply_markup = self._build_path_keyboard(context)
        if not reply_markup:
            await message.reply_text("No valid allowed paths are configured. Please check the .env file.")
            return ConversationHandler.END

        await message.reply_text(
            f"{message_}\nPlease select a valid allowed path:\n<blockquote>To add allowed paths, edit the <code>DOWNLOAD_PATH</code> in the .env file.</blockquote>",
            reply_markup=reply_markup, parse_mode="HTML"
        )
        return ASK_FILE_PATH

    async def upload3(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the selection of allowed paths for file upload. (Part3)"""
        query = update.callback_query
        if query is None or not query.data:
            return ConversationHandler.END

        await query.answer()

        parts = query.data.split(":", 2)
        if len(parts) != 3 or parts[0] != "up":
            await query.message.reply_text("Invalid upload selection.")
            return ConversationHandler.END

        _, file_token, path_token = parts
        src = context.user_data.get("uploaded_file_path")
        if not src or not os.path.isfile(src) or context.user_data.get("upload_file_token") != file_token:
            await query.message.reply_text("No file to upload. Please send a file first.")
            return ASK_FILE

        allowed_path = context.user_data.get("upload_path_map", {}).get(path_token)
        if not allowed_path:
            await query.message.reply_text("That upload destination is no longer available.\nPlease select another path.")
            return ASK_FILE_PATH

        if not is_path_allowed_download(allowed_path):
            await query.message.reply_text("Selected path is not allowed.")
            return ASK_FILE_PATH

        destination = os.path.join(allowed_path, os.path.basename(src))
        try:
            os.makedirs(allowed_path, exist_ok=True)
            os.replace(src, destination)
        except Exception as e:
            logger.error(f"Failed to move file to destination: {e}")
            await query.message.reply_text(f"Error moving file: {e}")
            return ConversationHandler.END

        await query.message.reply_text(f"File moved to {destination}")
        context.user_data.pop("upload_file_token", None)
        context.user_data.pop("uploaded_file_path", None)
        context.user_data.pop("upload_path_map", None)
        return ConversationHandler.END


    @restricted
    async def ls(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List the contents of a directory."""
        reload_settings()
        if not settings_core.ALLOWED_PATHS and not settings_core.DOWNLOAD_PATH:
            await update.message.reply_text("No allowed paths are configured. Please add allowed paths in the .env file.")
            return
        logger.debug(f"ALLOWED_PATHS: {settings_core.ALLOWED_PATHS}, DOWNLOAD_PATH: {settings_core.DOWNLOAD_PATH}")
        keyboard=[]
        for allowed_path in settings_core.ALLOWED_PATHS:
            allowed_path_cropped, valid = files_module.crop_file_path(allowed_path.replace("%USERPROFILE%", os.path.expanduser("~")))
            logger.debug(f"Allowed path: {allowed_path}, Cropped: {allowed_path_cropped}, Valid: {valid}")
            if valid:
                keyboard.append([InlineKeyboardButton(allowed_path_cropped, callback_data=f"ls:{allowed_path_cropped}")])
            else:
                logger.warning(f"Allowed path is not valid: {allowed_path} (cropped: {allowed_path_cropped})")
                
        for allowed_path in settings_core.DOWNLOAD_PATH:
            allowed_path_cropped, valid = files_module.crop_file_path(allowed_path.replace("%USERPROFILE%", os.path.expanduser("~")))
            logger.debug(f"Download path: {allowed_path}, Cropped: {allowed_path_cropped}, Valid: {valid}")
            if valid:
                keyboard.append([InlineKeyboardButton(allowed_path_cropped, callback_data=f"ls:{allowed_path_cropped}")])
            else:
                logger.warning(f"Download path is not valid: {allowed_path} (cropped: {allowed_path_cropped})")

        await update.message.reply_text("Select a path to list its contents:", reply_markup=InlineKeyboardMarkup(keyboard))
    @restricted
    async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mute the system audio."""
        result = audio.mute_audio()
        await update.message.reply_text(result[:200])
    @restricted
    async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unmute the system audio."""
        result = audio.unmute_audio()
        await update.message.reply_text(result[:200])
    @restricted
    @typeManagement
    async def writetype(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Write a string to the system keyboard."""
        if not context.args:
            await update.message.reply_text("Please provide a string to write. Usage: /type <string>")
            return
        text_to_write = " ".join(context.args)
        pyautogui.typewrite(text_to_write)
        await update.message.reply_text(f"<b>Typed:</b> \n<blockquote>{text_to_write}</blockquote>", parse_mode="HTML")
    @restricted
    @runCommand
    async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run a shell command on the server."""
        if not context.args:
            await update.message.reply_text("Please provide a command to run. Usage: /run <command>")
            return
        command = " ".join(context.args)
        result, error = await run_shell_command(command)
        if error:
            await update.message.reply_text(f"❌ Error running command:\n<code>{error}</code>", parse_mode="HTML")
            return
        await update.message.reply_text(f"<b>Command:</b> <code>{command}</code>\n<b>Output:</b>{'\n<blockquote>' + result + '</blockquote>' if result else '<i>N/A</i>'}", parse_mode="HTML")
    @restricted
    async def help_utility(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Provide help information for utility commands."""
        help_text = (
            "<b>Utility Commands:</b>\n"
            "/ls - List the contents of allowed directories.\n"
            "/upload - Upload a file to the server.\n"
            "/mute - Mute the system audio.\n"
            "/unmute - Unmute the system audio.\n"
            f"{escape('/type <string> - Type a string using the system keyboard.\n')}"
            f"{escape('/run <command> - Run a shell command on the server.\n')}"
        )
        message = update.effective_message
        if message:
            await message.reply_text(help_text, parse_mode="HTML")


def setup(app:Application):
    """Setup the file handlers for the Telegram bot."""
    create_temp_directory()

    app.add_handler(CommandHandler("ls", utilityCmd.ls))
    app.add_handler(CommandHandler("mute", utilityCmd.mute))
    app.add_handler(CommandHandler("unmute", utilityCmd.unmute))
    app.add_handler(CommandHandler("type", utilityCmd.writetype))
    app.add_handler(CommandHandler("run", utilityCmd.run))
    app.add_handler(CallbackQueryHandler(utilityCmd.help_utility, pattern="help_utility"))
    cmd = utilityCmd()
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("upload", restricted(cmd.upload))],
            states={
                ASK_FILE: [
                    MessageHandler(filters.Document.ALL | filters.PHOTO, restricted(cmd.upload2)),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, restricted(cmd.upload2)),  # catches plain text/invalid -> replies & stays in ASK_FILE

                ],
                ASK_FILE_PATH: [
                    CallbackQueryHandler(restricted(cmd.upload3))
                ]
            },
            fallbacks=[
                CommandHandler("upload", restricted(cmd.upload)),
            ],
            allow_reentry=True,
            per_chat=True
        )
    )