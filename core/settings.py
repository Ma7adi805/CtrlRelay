import os
from dotenv import load_dotenv

load_dotenv() 


def reload_settings():
    """Reload all settings from .env file"""
    load_dotenv(override=True)  # Force reload from .env
    
    # Update module-level variables
    global BOT_TOKEN, ALLOWED_CHAT_IDS, VOID_POWER_TIMER, POWER_TIMER_WAIT, POWER_MANAGEMENT
    global PROCESS_MANAGEMENT, SCREENSHOT_QUALITY
    global ALLOWED_PATHS, MAX_UPLOAD_SIZE, BLOCKED_EXTENSIONS, DOWNLOAD_PATH
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
    BLOCKED_EXTENSIONS = _list("BLOCKED_EXTENSIONS", ".exe,.bat,.ps1,.msi,.cmd,.vbs,.reg")
    DOWNLOAD_PATH = _list("DOWNLOAD_PATH", "C:/Users/Public/Downloads/CtrlRelay")
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
BLOCKED_EXTENSIONS: list[str] = _list("BLOCKED_EXTENSIONS", ".exe,.bat,.ps1,.msi,.cmd,.vbs,.reg")
DOWNLOAD_PATH: list[str] = _list("DOWNLOAD_PATH", "C:/Users/Public/Downloads/CtrlRelay")
 
# Input
RUN_COMMAND_ENABLED: bool = _bool("RUN_COMMAND_ENABLED", True)
TYPE_ENABLED: bool = _bool("TYPE_ENABLED", True)
 
# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE: str = os.getenv("LOG_FILE", "ctrlrelay.log")
 
