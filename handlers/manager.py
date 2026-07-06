import subprocess, platform, asyncio
from time import time
from core.auth import restricted, power
import core.settings as settings_core
from core.settings import reload_settings
from utils.logger import logger
from telegram import Update
from telegram.ext import ContextTypes
from time import sleep as time_sleep
from PIL import ImageGrab, Image
import os


def take_screenshot() -> Image.Image:
    """Take a screenshot of the specified monitor and save it as a PNG file."""
    quality = settings_core.SCREENSHOT_QUALITY
    monitor_index = settings_core.MONITOR_INDEX

    bbox = None

    # Capture selected monitor if configured (Windows)
    if platform.system() == "Windows" and isinstance(monitor_index, int) and monitor_index >= 0:
        try:
            import ctypes
            from ctypes import wintypes

            monitors: list[tuple[int, int, int, int]] = []

            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_int,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                wintypes.LPARAM,
            )

            def _enum_proc(hmonitor, hdc, lprect, lparam):
                rect = lprect.contents
                monitors.append((rect.left, rect.top, rect.right, rect.bottom))
                return 1

            ctypes.windll.user32.EnumDisplayMonitors(
                0,
                0,
                MONITORENUMPROC(_enum_proc),
                0,
            )

            if 0 <= monitor_index < len(monitors):
                bbox = monitors[monitor_index]
        except Exception as e:
            logger.warning(f"Failed to resolve monitor index {monitor_index}: {e}")

    # Capture the screen (selected monitor or full screen)
    screenshot = ImageGrab.grab(bbox=bbox, all_screens=bbox is None)

    # Apply quality (for non-JPEG workflows, reduce color depth when quality is lower)
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

def launch_application(app_name) -> str:
    """Launch an application using the provided command."""
    try:
        subprocess.Popen(app_name, shell=True)
        return f"Application '{app_name}' launched successfully."
    except Exception as e:
        logger.error(f"Failed to launch application '{app_name}': {e}")
        return f"Failed to launch application '{app_name}': {e}"

class ManagerHandler:
    @restricted
    async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Take a screenshot of the specified monitor and send it to the user."""
        reload_settings() 
        start_time = time()
        logger.info("Taking screenshot...")
        screenshot = take_screenshot()
        screenshot_path = "screenshot.jpg"
        screenshot.save(
            screenshot_path,
            "JPEG",
            quality=max(1, min(100, int(settings_core.SCREENSHOT_QUALITY))),
            optimize=True,
        )
        logger.info(f"Screenshot taken in {time() - start_time:.2f} seconds.")
        
        # Send the screenshot to the user
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(screenshot_path, 'rb'))
        
        # Clean up the saved screenshot file
        os.remove(screenshot_path)
    @restricted
    async def sysinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send system information to the user."""
        info = sysinfo()
        await update.message.reply_text(f"<b>System Information:</b>\n\n{info}", parse_mode="HTML")