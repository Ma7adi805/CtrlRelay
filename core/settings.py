import os, sys
from pathlib import Path
from dotenv import load_dotenv

def get_log_path():
    """
    Get the appropriate log file path.
    - Portable mode (EXE folder writable): log next to EXE
    - Installed mode (Program Files): log in AppData
    """
    try:
        # Try to get the directory where the EXE/script is located
        exe_path = Path(os.path.abspath(__file__)).parent
        log_in_exe_dir = exe_path / "ctrlrelay.log"

        # Try to write to EXE folder
        with open(log_in_exe_dir, 'a'):
            pass
        return str(log_in_exe_dir)
    except (PermissionError, OSError):
        # Can't write to EXE folder (installed mode), use AppData
        appdata = Path(os.getenv('APPDATA', '')) / 'CtrlRelay'
        appdata.mkdir(parents=True, exist_ok=True)
        return str(appdata / 'ctrlrelay.log')

load_dotenv() 

def setup_env():
    # Get the proper .env path (same location as EXE)
    if getattr(sys, 'frozen', False):
        # Running as EXE
        env_path = os.path.join(os.path.dirname(sys.executable), ".env")
    else:
        # Running as script
        env_path = ".env"

    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        # Create a default .env file if it doesn't exist
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                Format = r"""# CtrlRelay Configuration Template
# Copy this file to .env and fill in your values

# --- Auth ---
TELEGRAM_TOKEN=your_telegram_bot_token_here  # Get from @BotFather
ALLOWED_CHAT_IDS=your_telegram_chat_id_here  # Comma-separated, get from /start command

# --- Power Settings ---
VOID_POWER_TIMER=true        # Show cancel window before shutdown/restart/sleep
POWER_TIMER_WAIT=30        # Seconds to wait before executing power command
POWER_MANAGEMENT=true      # Enable /processes, /kill, /launch, /setaudio

# --- System ---
PROCESS_MANAGEMENT=true      # Enable /processes, /kill, /launch, /setaudio
SCREENSHOT_QUALITY=85    # JPEG quality 1-100

# --- Files ---
ALLOWED_PATHS=   # Comma-separated paths for /ls command (e.g. C:\Users\USERNAME\Downloads\,C:\Users\USERNAME\Documents)
MAX_UPLOAD_SIZE=48             # Max file size in MB (Telegram bot limit is 50MB)
BLOCKED_EXTENSIONS= # Comma-separated file extensions to block (e.g. .exe,.bat,.cmd)
DOWNLOAD_PATH=%USERPROFILE%\Downloads\CtrlRelay  # Path for downloaded files (for /upload and /getfile commands). If empty, defaults to C:/Users/Public/Downloads/CtrlRelay

# --- Input ---
RUN_COMMAND_ENABLED=false     # Enable /run (shell command execution) - SECURITY RISK: Set to true only if needed and understood
TYPE_ENABLED=true            # Enable /type (remote keyboard input)

# --- Logging  ---
LOG_LEVEL=INFO               # DEBUG, INFO, ERROR
LOG_FILE=ctrlrelay.log"""
                f.write(Format)
                del Format
            from bot_utils.logger import logger
            logger.info("Created default .env file. Please configure it before running the bot.")
        except PermissionError:
            # Can't create .env, app will fail gracefully later when config is missing
            pass

        # Load the newly created .env file
        load_dotenv(dotenv_path=env_path)

def reload_settings():
    """Reload all settings from .env file"""
    from bot_utils.logger import logger
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
    BLOCKED_EXTENSIONS = _list("BLOCKED_EXTENSIONS")
    DOWNLOAD_PATH = _list("DOWNLOAD_PATH", r"%USERPROFILE%\Downloads\CtrlRelay")
    RUN_COMMAND_ENABLED = _bool("RUN_COMMAND_ENABLED", True)
    TYPE_ENABLED = _bool("TYPE_ENABLED", True)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE = get_log_path()  # Auto-detect: EXE folder or AppData


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
BLOCKED_EXTENSIONS: list[str] = _list("BLOCKED_EXTENSIONS")
DOWNLOAD_PATH: list[str] = _list("DOWNLOAD_PATH", r"%USERPROFILE%\Downloads\CtrlRelay")
 
# Input
RUN_COMMAND_ENABLED: bool = _bool("RUN_COMMAND_ENABLED", True)
TYPE_ENABLED: bool = _bool("TYPE_ENABLED", True)
 
# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE: str = get_log_path()  # Auto-detect: EXE folder or AppData
 
