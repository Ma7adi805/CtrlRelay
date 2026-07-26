import subprocess, platform, asyncio, os, json, psutil
from time import time
from core.auth import restricted, power
import core.settings as settings_core
from core.settings import reload_settings
from utils.logger import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, Application, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from html import escape
from time import sleep as time_sleep
from PIL import ImageGrab, Image
import configs.launch.add_launch_shortcuts as launch_shortcuts
from core.auth import processManagement
import modules.audio as audio_module

ASK_PATH = 1

def take_screenshot() -> Image.Image:
    """Take a screenshot of the full desktop (all monitors)."""
    quality = settings_core.SCREENSHOT_QUALITY

    # Always capture the full desktop across all monitors
    screenshot = ImageGrab.grab(all_screens=True)
    try:
        quality = max(1, min(100, int(quality)))
    except Exception:
        quality = 100

    if quality < 100:
        colors = max(16, int(256 * (quality / 100)))
        screenshot = screenshot.convert("P", palette=Image.ADAPTIVE, colors=colors).convert("RGB")
    
    return screenshot

def sysinfo() -> str:
    """Return system information as a string."""
    try:
        uname = platform.uname()
        return (
            f"<b>System:</b> {uname.system}\n"
            f"<b>Node Name:</b> {uname.node}\n"
            f"<b>Release:</b> {uname.release}\n"
            f"<b>Version:</b> {uname.version}\n"
            f"<b>Machine:</b> {uname.machine}\n"
            f"<b>Processor:</b> {uname.processor}\n"
            f"<b>Platform:</b> {platform.platform()}\n"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve system information: {e}")
        return "System information not available."



class ManagerHandler:
    @restricted
    @processManagement
    async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Take a screenshot of the full desktop and send it to the user."""
        reload_settings() 
        start_time = time()
        logger.info("Taking screenshot...")
        screenshot = take_screenshot()
        if screenshot is None:
            await update.message.reply_text("Failed to take a screenshot.")
            return
        screenshot_path = f"screenshot_{int(time())}.jpg"
        screenshot.save(
            screenshot_path,
            "JPEG",
            quality=max(1, min(100, int(settings_core.SCREENSHOT_QUALITY))),
            optimize=True,
        )
        logger.info(f"Screenshot taken in {time() - start_time:.2f} seconds.")
        
        # Send the screenshot to the user
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(screenshot_path, 'rb'))
        
        os.remove(screenshot_path)

    @restricted
    @processManagement
    async def sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send system information to the user."""
        info = sysinfo()
        await update.message.reply_text(f"<b>System Information:</b>\n\n{info}", parse_mode="HTML")

    @restricted
    @processManagement
    async def launch_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Launch an application using a specified shortcut."""
        shortcuts = launch_shortcuts.list_shortcuts()
        if not shortcuts:
            await update.message.reply_text("No launch shortcuts are configured.")
            return

        keyboard = []
        for name, shortcut_data in shortcuts.items():
            logger.debug(f"Adding shortcut to keyboard: {name} -> ID: {shortcut_data['id']}")
            keyboard.append([
                InlineKeyboardButton(name, callback_data=f"launch:{shortcut_data['id']}")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select a shortcut to launch:", reply_markup=reply_markup)
    @restricted
    @processManagement
    async def delete_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a launch shortcut."""
        shortcuts = launch_shortcuts.list_shortcuts()
        if not shortcuts:
            await update.message.reply_text("No launch shortcuts are configured.")
            return

        keyboard = []
        for name, shortcut_data in shortcuts.items():
            logger.debug(f"Adding delete option to keyboard: {name} -> ID: {shortcut_data['id']}")
            keyboard.append([
                InlineKeyboardButton(f"Delete {name}", callback_data=f"delete:{shortcut_data['id']}")
            ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Select a shortcut to delete:", reply_markup=reply_markup)
    
    @restricted
    @processManagement
    async def create_shortcut(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new launch shortcut."""
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /create_shortcut <name> ")
            return
        name = context.args[0]
        context.user_data["shortcut_name"] = name

        await update.message.reply_text("Please send the command or path for the shortcut.")
        return ASK_PATH
    
    @restricted
    @processManagement
    async def create_shortcut2(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new launch shortcut. (Part 2: Receive the command/path)"""
        path = update.message.text
        name = context.user_data.get("shortcut_name")
        if not name or not path:
            await update.message.reply_text("Shortcut name or path is missing. Please start over.")
            return ConversationHandler.END
        response = launch_shortcuts.add_shortcut(name, path)
        await update.message.reply_text(response)
        return ConversationHandler.END
    
    @restricted
    @processManagement
    async def setaudio(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the default audio output device."""
        audios = audio_module.get_clean_output_devices()
        current_volume= audio_module.get_audio_volume()
        current_volume = current_volume if current_volume is not None else "Unknown"
        audio_keyboard = []
        for device in audios:
            audio_keyboard.append([
                InlineKeyboardButton(f"{device['name'][:30]} ({device['original_index']})", callback_data=f"setaudio:{device['original_index']}")
            ])
        reply_markup = InlineKeyboardMarkup(audio_keyboard)

        currentAudio = audio_module.get_default_output_device()
        currentAudio = currentAudio['name'] if currentAudio else "Unknown"
        await update.message.reply_text(f"Select an audio output device:\n<b>Current Audio Output:</b> {currentAudio[:60]}\n<b>Current Volume:</b> {current_volume}%", reply_markup=reply_markup, parse_mode="HTML")
    
    @restricted
    @processManagement
    async def volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the system audio volume."""
        if len(context.args) < 1:
            await update.message.reply_text("Usage: /volume <volume>\nVolume should be a number between 0 and 100.")
            return

        try:
            volume = context.args[0]
            volume = volume.replace("%", "")  
            volume = int(volume)
            if not (0 <= volume <= 100):
                raise ValueError("Volume must be between 0 and 100.")
        except ValueError as e:
            await update.message.reply_text(f"Invalid volume value: {e}")
            return

        result = audio_module.set_audio_volume(volume)
        await update.message.reply_text(result)
    
    @restricted
    @processManagement
    async def processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List running processes."""

        procs = []
        for proc in psutil.process_iter():
            try:
                procs.append(proc)
                proc.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        await asyncio.sleep(0.1)

        processes = []
        for proc in procs:
            try:
                processes.append({
                    'pid': proc.pid,
                    'name': proc.name()[:30],
                    'cpu': proc.cpu_percent(),
                    'mem': proc.memory_percent(),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes.sort(key=lambda p: p['cpu'], reverse=True)

        lines = ["<b>Top Processes (by CPU):</b>\n"]
        for p in processes[:15]:
            lines.append(
                f"<code>{p['pid']:>6}</code>  "
                f"{p['cpu']:5.1f}%  "
                f"{p['mem']:4.1f}%  "
                f"{p['name']}"
            )
        lines.append(escape("\n/kill <pid> to terminate"))

        await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    @restricted
    @processManagement
    async def kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) == 1:
            pid = int(context.args[0])
            proc = psutil.Process(pid)
            name = proc.name()
            proc.kill()
            await update.message.reply_text(f"Killed process {pid} ({name})")
            return
        else:
            await update.message.reply_text("Usage: /kill <pid>")
        
    @restricted
    async def help_process_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a help message for process management commands."""
        reload_settings()
        enabled = settings_core.PROCESS_MANAGEMENT

        commands_text = (
            "<b>Process Management Commands:</b>\n"
            "/screenshot - Take a screenshot of the full desktop.\n"
            "/sysinfo - Get system information.\n"
            "/launch_shortcut - Launch an application using a configured shortcut.\n"
            "/delete_shortcut - Delete a configured launch shortcut.\n"
            f"{escape('/create_shortcut <name> - Create a new launch shortcut (you will be prompted for the command/path).')}\n"
            "/setaudio - Set the default audio output device. <i>(BETA)</i>\n"
            f"{escape('/volume <volume> - Set the system audio volume (1-100).')} <i>(BETA)</i>\n"
            "/processes - List top processes by CPU usage.\n"
            f"{escape('/kill <pid> - Terminate a process.')}\n"
        )
        disclaimer = (
            "\nDisclaimer: Process management commands are currently disabled in the .env file. "
            "Please enable <code>PROCESS_MANAGEMENT</code> in the .env file to use these commands."
        )

        help_text = commands_text + (disclaimer if not enabled else "")
        message = update.effective_message
        if message:
            await message.reply_text(help_text, parse_mode="HTML")
def setup(app:Application):
    """Set up the ManagerHandler commands."""
    app.add_handler(CommandHandler("screenshot", ManagerHandler.screenshot))
    app.add_handler(CommandHandler("sysinfo", ManagerHandler.sysinfo))
    app.add_handler(CommandHandler("launch_shortcut", ManagerHandler.launch_shortcut))
    app.add_handler(CommandHandler("delete_shortcut", ManagerHandler.delete_shortcut))
    app.add_handler(CommandHandler("setaudio", ManagerHandler.setaudio))
    app.add_handler(CommandHandler("volume", ManagerHandler.volume))
    app.add_handler(CommandHandler("processes", ManagerHandler.processes))
    app.add_handler(CommandHandler("kill", ManagerHandler.kill))
    app.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("create_shortcut", ManagerHandler.create_shortcut)],
            states={
                ASK_PATH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, ManagerHandler.create_shortcut2)
                ]
            },
            fallbacks=[],
        )
    )
    app.add_handler(CallbackQueryHandler(ManagerHandler.help_process_command, pattern="help_process"))