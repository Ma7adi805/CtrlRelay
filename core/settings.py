import os
from dotenv import load_dotenv
load_dotenv() 

def setup_env():
    if os.path.exists(".env"):
        load_dotenv()
    else:
        # Create a default .env file if it doesn't exist
        from utils.logger import logger
        with open(".env", "w", encoding="utf-8") as f:
            Format = r"""# CtrlRelay Configuration

# --- Auth ---
TELEGRAM_TOKEN= # Your Telegram bot token (Get it from @BotFather)
ALLOWED_CHAT_IDS=   # Comma-separated Telegram chat IDs (e.g., 123456789,987654321) (Use /setup to get your chat ID)

# --- Power Settings ---
VOID_POWER_TIMER=true        # Show cancel window before shutdown/restart/sleep
POWER_TIMER_WAIT=30       # Seconds to wait before executing power command
POWER_MANAGEMENT=true      # Enable /processes, /kill, /launch, /setaudio
# --- System ---
PROCESS_MANAGEMENT=true      # Enable /processes, /kill, /launch, /setaudio
SCREENSHOT_QUALITY=80    # JPEG quality 1-100

# --- Files ---
ALLOWED_PATHS=y   # Comma-separated, restricts /ls (ex.  C:\Users\[USER]\Downloads\,C:\Users\[USER]\Documents)
MAX_UPLOAD_SIZE=48             # Max file size in MB (Telegram bot limit is 50MB)
DOWNLOAD_PATH=%USERPROFILE%\Downloads\CtrlRelay  # Path for downloaded files (for /upload and /getfile commands). If empty, defaults to C:/Users/Public/Downloads/CtrlRelay

# --- Input ---
RUN_COMMAND_ENABLED=true     # Enable /run (shell command execution)
TYPE_ENABLED=true            # Enable /type (remote keyboard input)

# --- Logging  ---
LOG_LEVEL=INFO               # DEBUG, INFO, ERROR
LOG_FILE=ctrlrelay.log"""
            f.write(Format)
            del Format
            logger.info("Created default .env file. Please configure it before running the bot.")

def reload_settings():
    """Reload all settings from .env file"""
    from utils.logger import logger
    load_dotenv(override=True)  # Force reload from .env

    # Update module-level variables
    global BOT_TOKEN, ALLOWED_CHAT_IDS, VOID_POWER_TIMER, POWER_TIMER_WAIT, POWER_MANAGEMENT
    global PROCESS_MANAGEMENT, SCREENSHOT_QUALITY
    global ALLOWED_PATHS, MAX_UPLOAD_SIZE, DOWNLOAD_PATH
    global RUN_COMMAND_ENABLED, TYPE_ENABLED, LOG_LEVEL, LOG_FILE

    BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    ALLOWED_CHAT_IDS = [int(x) for x in _list("ALLOWED_CHAT_IDS") if x.isdigit()]
    VOID_POWER_TIMER = _bool("VOID_POWER_TIMER", True)
    POWER_TIMER_WAIT = _int("POWER_TIMER_WAIT", 10)
    POWER_MANAGEMENT = _bool("POWER_MANAGEMENT", True)
    PROCESS_MANAGEMENT = _bool("PROCESS_MANAGEMENT", True)
    SCREENSHOT_QUALITY = _int("SCREENSHOT_QUALITY", 85)
    ALLOWED_PATHS = _list("ALLOWED_PATHS")
    MAX_UPLOAD_SIZE = _int("MAX_UPLOAD_SIZE", 48)
    DOWNLOAD_PATH = _list("DOWNLOAD_PATH", r"%USERPROFILE%\Downloads\CtrlRelay")
    RUN_COMMAND_ENABLED = _bool("RUN_COMMAND_ENABLED", True)
    TYPE_ENABLED = _bool("TYPE_ENABLED", True)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = os.getenv("LOG_FILE", "ctrlrelay.log")


def _bool(key: str, default: bool = True) -> bool:
    return os.getenv(key, str(default)).lower() in ("true", "1", "yes")
 
def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except (ValueError, TypeError):
        return default
    
def _list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key)
    if raw is None:
        raw = default          # env var not set → use default
    elif '#' in raw:
        raw = raw.split('#', 1)[0].strip()  # strip inline comments
    return [x.strip() for x in raw.split(",") if x.strip()] if raw else []

# Auth
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
ALLOWED_CHAT_IDS: list[int] = [int(x) for x in _list("ALLOWED_CHAT_IDS") if x.isdigit()]

# Power
VOID_POWER_TIMER: bool = _bool("VOID_POWER_TIMER", True)
POWER_TIMER_WAIT: int = _int("POWER_TIMER_WAIT", 10)
POWER_MANAGEMENT: bool = _bool("POWER_MANAGEMENT", True)
# System
PROCESS_MANAGEMENT: bool = _bool("PROCESS_MANAGEMENT", True)
SCREENSHOT_QUALITY: int = _int("SCREENSHOT_QUALITY", 85)
 
# Files
ALLOWED_PATHS: list[str] = _list("ALLOWED_PATHS")
MAX_UPLOAD_SIZE: int = _int("MAX_UPLOAD_SIZE", 48)
DOWNLOAD_PATH: list[str] = _list("DOWNLOAD_PATH", r"%USERPROFILE%\Downloads\CtrlRelay")
 
# Input
RUN_COMMAND_ENABLED: bool = _bool("RUN_COMMAND_ENABLED", True)
TYPE_ENABLED: bool = _bool("TYPE_ENABLED", True)
 
# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE: str = os.getenv("LOG_FILE", "ctrlrelay.log")
 
