import threading, os, pystray, asyncio, inspect
from enum import Enum
from PIL import Image, ImageDraw

DEFAULT_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CtrlRelay.log")
ENV = DEFAULT_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

basedir = os.path.dirname(os.path.abspath(__file__))

iconsdir = os.path.join(basedir, "icons")

class TrayIcons(Enum):
    STARTING = Image.open(iconsdir + "/Starting.png")
    RUNNING = Image.open(iconsdir + "/Running.png")
    STOPPED = Image.open(iconsdir + "/Stopped.png")
    STOPPING = Image.open(iconsdir + "/Stopping.png")
    ERROR = Image.open(iconsdir + "/ERROR.png")

class Action(Enum):
    START = "Start"
    RESTART = "Restart"
    STOP = "Stop"

class Status(Enum):
    RUNNING = "Running"
    STARTING = "Starting"
    STOPPING = "Stopping"
    ERROR = "Error"
    STOPPED = "Stopped"

_current_status = Status.STOPPED
_icon = None
_power_event_callback = None
_quit_callback = None

def onPowerEvent(func):
    global _power_event_callback
    _power_event_callback = func
    return func

def onQuit(func):
    global _quit_callback
    _quit_callback = func
    return func

def set_icon(icon: TrayIcons):
    global _icon
    if _icon:
        _icon.icon = icon.value
        

def update_status(new_status: Status):
    global _current_status, _icon
    _current_status = new_status
    if _icon:
        set_icon(TrayIcons[new_status.name])
        _icon.menu = _build_menu()

def _log_exists():
    """Checks if the log file exists. Returns True if it does, False otherwise."""
    # Implement the logic to check for the existence of the log file
    return os.path.exists(DEFAULT_LOG_FILE)

def open_logs():
    """Opens the log file in the default text editor. (If Exists)"""
    if _log_exists():
        os.startfile(DEFAULT_LOG_FILE)
    else:
        print("Log file does not exist.")

def open_env():
    """Opens the environment variables window."""
    os.startfile(ENV)

def _handle_action(action: Action):
    if not _power_event_callback:
        return

    def run_callback():
        if inspect.iscoroutinefunction(_power_event_callback):
            asyncio.run(_power_event_callback(action))
        else:
            _power_event_callback(action)

    threading.Thread(target=run_callback, daemon=True).start()

def _handle_quit(icon, item):
    if _quit_callback:
        if inspect.iscoroutinefunction(_quit_callback):
            asyncio.run(_quit_callback())
        else:
            _quit_callback()
    icon.stop()

def _build_menu():
    sts = f"Status: {_current_status.value}"
    sts_enabled = False
    if _current_status == Status.ERROR:
        sts += " (Open Logs)"
        if _log_exists():
            sts_enabled = True
    return pystray.Menu(
        pystray.MenuItem('CtrlRelay', None, enabled=False),
        pystray.MenuItem(sts, enabled=sts_enabled, action=open_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            'Start', 
            lambda icon, item: _handle_action(Action.START), 
            enabled=_current_status in [Status.STOPPED, Status.ERROR]
        ),
        pystray.MenuItem(
            'Restart', 
            lambda icon, item: _handle_action(Action.RESTART), 
            enabled=_current_status == Status.RUNNING
        ),
        pystray.MenuItem(
            'Stop', 
            lambda icon, item: _handle_action(Action.STOP), 
            enabled=_current_status in [Status.RUNNING, Status.STARTING]
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Open .env', open_env, enabled=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Quit', _handle_quit)
    )



def run():
    global _icon
    _icon = pystray.Icon("CtrlRelay", menu=_build_menu(), icon=TrayIcons.STOPPED.value)
    _icon.run()