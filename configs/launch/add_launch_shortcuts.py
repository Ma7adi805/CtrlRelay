import os, json, subprocess, platform, shlex, shutil, sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.settings import reload_settings
import core.settings as settings_core
from bot_utils.logger import logger

LAUNCH_JSON_PATH = Path(__file__).resolve().with_name("launch.json")

def setup_file():
    json_format_default = {
        "launch_shortcuts": {}
    }

    if not LAUNCH_JSON_PATH.exists():
        print("Creating default launch.json configuration file...")
        with LAUNCH_JSON_PATH.open("w", encoding="utf-8") as f:
            json.dump(json_format_default, f, indent=4)

setup_file()

def get_id(id:int) -> str | None:
    """Get the shortcut name by its ID."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        for name, shortcut_data in data.get("launch_shortcuts", {}).items():
            if shortcut_data.get("id") == id:
                return name
        return None
    except Exception as e:
        logger.error(f"Failed to get shortcut name by ID: {e}")
        return None

def get_next_id() -> int:
    """Get the next available ID for a new shortcut."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        existing_ids = [value['id'] for value in data.get("launch_shortcuts", {}).values() if isinstance(value['id'], int)]
        next_id = max(existing_ids, default=0) + 1
        return next_id
    except Exception as e:
        logger.error(f"Failed to get next ID: {e}")
        return 1


def _strip_wrapping_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _resolve_launch_target(command: str) -> tuple[str, list[str]]:
    try:
        parts = shlex.split(command, posix=(platform.system() != "Windows"))
    except Exception:
        parts = command.split()

    if not parts:
        return "", []

    executable = _strip_wrapping_quotes(os.path.expanduser(os.path.expandvars(parts[0])))
    arguments = [_strip_wrapping_quotes(part) for part in parts[1:]]
    return executable, arguments

def is_valid_shortcut_cmd(command: str) -> tuple[bool, str]:
    """Check if the shortcut command is valid."""
    reload_settings()  # Ensure settings are up to date
    if not command or command.isdigit():
        return False, "Command is empty or contains only digits."

    exe_path, _arguments = _resolve_launch_target(command)
    if not exe_path:
        return False, "Command is empty or contains only digits."

    ext = Path(exe_path).suffix.lower()
    blocked_extensions = {item.lower() for item in settings_core.BLOCKED_EXTENSIONS}
    if ext and ext in blocked_extensions:
        return False, f"Extension '{ext}' is currently blocked, please remove it from the BLOCKED_EXTENSIONS in the .env file to allow this command."

    if platform.system() == "Windows" and os.path.isfile(exe_path):
        return True, "Command is valid."

    # If it's a path to a file, check it exists and is executable (or has an executable extension on Windows)
    if os.path.isabs(exe_path) or os.path.dirname(exe_path):
        if os.path.isfile(exe_path):
            if os.access(exe_path, os.X_OK) or platform.system() == "Windows":
                return True, "Command is valid."
        # Try adding common executable extensions on Windows
        if platform.system() == "Windows":
            for ext in [".exe", ".bat", ".cmd", ".com", ".ps1", ".vbs", ".msi", ".py", ".lnk", ".url"]:
                candidate = exe_path if ext == Path(exe_path).suffix.lower() else exe_path + ext
                if os.path.isfile(candidate):
                    return True, "Command is valid."

    # Otherwise, check if executable is on PATH
    if shutil.which(exe_path):
        return True, "Command is valid."

    return False, f"Command '{command}' is not valid or executable."
    
    

def list_shortcuts() -> dict:
    """List all launch shortcuts from the configuration file."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("launch_shortcuts", {})
    except Exception as e:
        logger.error(f"Failed to read launch shortcuts: {e}")
        return {}

def add_shortcut(name: str, command: str) -> str:
    """Add a new launch shortcut to the configuration file."""
    try:
        if name in list_shortcuts():
            return f"Shortcut '{name}' already exists."
        if name.isdigit():
            return f"Shortcut name '{name}' cannot be a number."
        is_valid, validation_message = is_valid_shortcut_cmd(command)
        if not is_valid:
            return validation_message
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        if name in data.get("launch_shortcuts", {}):
            return f"Shortcut '{name}' already exists."
        
        next_id = get_next_id()
        data["launch_shortcuts"][name] = {"command": command, "id": next_id}
        
        with LAUNCH_JSON_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Added new shortcut: {name} -> Command: {command} --> ID: {next_id}")
        return f"Shortcut '{name}' added successfully."
    except Exception as e:
        logger.error(f"Failed to add launch shortcut: {e}")
        return f"Failed to add shortcut '{name}': {e}"

def remove_shortcut_by_id(shortcut_id: int) -> str:
    """Remove a launch shortcut by its ID."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        for name, shortcut_data in list(data.get("launch_shortcuts", {}).items()):
            if shortcut_data.get("id") == shortcut_id:
                del data["launch_shortcuts"][name]
                with LAUNCH_JSON_PATH.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                logger.info(f"Removed shortcut: {name} with ID: {shortcut_id}")
                return f"Shortcut '{name}' removed successfully."
        
        return f"Shortcut with ID '{shortcut_id}' does not exist."
    except Exception as e:
        logger.error(f"Failed to remove launch shortcut by ID: {e}")
        return f"Failed to remove shortcut with ID '{shortcut_id}': {e}"
    
def remove_shortcut_by_name(name: str) -> str:
    """Remove a launch shortcut by its name."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        if name not in data.get("launch_shortcuts", {}):
            return f"Shortcut '{name}' does not exist."
        
        del data["launch_shortcuts"][name]
        
        with LAUNCH_JSON_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Removed shortcut: {name}")
        return f"Shortcut '{name}' removed successfully."
    except Exception as e:
        logger.error(f"Failed to remove launch shortcut by name: {e}")
        return f"Failed to remove shortcut '{name}': {e}"



def get_shortcut_by_id(shortcut_id: int) -> tuple[str | None, str | None]:
    """Get a launch shortcut by its ID."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        for name, shortcut_data in data.get("launch_shortcuts", {}).items():
            if shortcut_data.get("id") == shortcut_id:
                return name, shortcut_data.get("command")
        return None, None
    except Exception as e:
        logger.error(f"Failed to get shortcut by ID: {e}")
        return None, None


def launch_shortcut_by_id(shortcut_id: int) -> str:
    """Launch a shortcut by its ID."""
    name, command = get_shortcut_by_id(shortcut_id)
    if not name or not command:
        return f"Shortcut with ID '{shortcut_id}' does not exist."

    is_valid, validation_message = is_valid_shortcut_cmd(command)
    if not is_valid:
        return validation_message

    try:
        if platform.system() == "Windows":
            # On Windows with shell=True, pass the command as a single string
            subprocess.Popen(command, shell=True)
        else:
            # On Unix-like systems, use the list approach
            exe_path, arguments = _resolve_launch_target(command)
            subprocess.Popen([exe_path] + arguments)
        logger.info(f"Launched shortcut '{name}' with command: {command}")
        return f"Shortcut '{name}' launched successfully."
    except Exception as e:
        logger.error(f"Failed to launch shortcut '{name}': {e}")
        return f"Failed to launch shortcut '{name}': {e}"
    
def launch_shortcut_by_name(name: str) -> str:
    """Launch a shortcut by its name."""
    try:
        with LAUNCH_JSON_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        shortcut_data = data.get("launch_shortcuts", {}).get(name)
        if not shortcut_data:
            return f"Shortcut '{name}' does not exist."

        command = shortcut_data.get("command")
        is_valid, validation_message = is_valid_shortcut_cmd(command)
        if not is_valid:
            return validation_message

        try:
            if platform.system() == "Windows":
                # On Windows with shell=True, pass the command as a single string
                subprocess.Popen(command, shell=True)
            else:
                # On Unix-like systems, use the list approach
                exe_path, arguments = _resolve_launch_target(command)
                subprocess.Popen([exe_path] + arguments)
            logger.info(f"Launched shortcut '{name}' with command: {command}")
            return f"Shortcut '{name}' launched successfully."
        except Exception as e:
            logger.error(f"Failed to launch shortcut '{name}': {e}")
            return f"Failed to launch shortcut '{name}': {e}"
    except Exception as e:
        logger.error(f"Failed to launch shortcut '{name}': {e}")
        return f"Failed to launch shortcut '{name}': {e}"

if __name__ == "__main__":
    while True:
        print("\nLaunch Shortcuts Management")
        print("1. List Shortcuts")
        print("2. Add Shortcut")
        print("3. Remove Shortcut")
        print("4. Launch Shortcut")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            shortcuts = list_shortcuts()
            if not shortcuts:
                print("No shortcuts available.")
            else:
                for name, command in shortcuts.items():
                    print(f"Shortcut: {name} -> Command: {command['command']} --> ID: {command['id']}")
        
        elif choice == "2":
            name = input("Enter shortcut name: ")
            command = input("Enter command to launch: ")
            result = add_shortcut(name, command)
            print(result)
        
        elif choice == "3":
            name = input("Enter shortcut name to remove: ")
            result = remove_shortcut_by_name(name)
            print(result)
        
        elif choice == "4":
            name = input("Enter shortcut name to launch: ")
            result = launch_shortcut_by_name(name)
            print(result)
        
        elif choice == "5":
            print("Exiting Launch Shortcuts Management.")
            break
        
        else:
            print("Invalid choice. Please try again.")