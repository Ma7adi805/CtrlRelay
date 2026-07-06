import os, json, subprocess, platform


json_format_default = {
    "launch_shortcuts": {}
}

if not os.path.exists("configs/launch/launch.json"):
    print("Creating default launch.json configuration file...")
    with open("configs/launch/launch.json", "w") as f:
        json.dump(json_format_default, f, indent=4)
    
def list_shortcuts() -> dict:
    """List all launch shortcuts from the configuration file."""
    try:
        with open("configs/launch/launch.json", "r") as f:
            data = json.load(f)
        for key, value in data.get("launch_shortcuts", {}).items():
            print(f"Shortcut: {key} -> Command: {value}")
        return data.get("launch_shortcuts", {})
    except Exception as e:
        print(f"Failed to read launch shortcuts: {e}")
        return {}

def add_shortcut(name: str, command: str) -> str:
    """Add a new launch shortcut to the configuration file."""
    try:
        with open("configs/launch/launch.json", "r") as f:
            data = json.load(f)
        
        if name in data.get("launch_shortcuts", {}):
            return f"Shortcut '{name}' already exists."
        
        data["launch_shortcuts"][name] = command
        
        with open("configs/launch/launch.json", "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Added new shortcut: {name} -> Command: {command}")
        return f"Shortcut '{name}' added successfully."
    except Exception as e:
        print(f"Failed to add launch shortcut: {e}")
        return f"Failed to add shortcut '{name}': {e}"

def remove_shortcut(name: str) -> str:
    """Remove a launch shortcut from the configuration file."""
    try:
        with open("configs/launch/launch.json", "r") as f:
            data = json.load(f)
        
        if name not in data.get("launch_shortcuts", {}):
            return f"Shortcut '{name}' does not exist."
        
        del data["launch_shortcuts"][name]
        
        with open("configs/launch/launch.json", "w") as f:
            json.dump(data, f, indent=4)
        
        print(f"Removed shortcut: {name}")
        return f"Shortcut '{name}' removed successfully."
    except Exception as e:
        print(f"Failed to remove launch shortcut: {e}")
        return f"Failed to remove shortcut '{name}': {e}"

def launch_shortcut(name: str) -> str:
    """Launch an application using the specified shortcut."""
    try:
        with open("configs/launch/launch.json", "r") as f:
            data = json.load(f)
        
        command = data.get("launch_shortcuts", {}).get(name)
        if not command:
            return f"Shortcut '{name}' does not exist."
        
        subprocess.Popen(command, shell=True)
        print(f"Launched application using shortcut: {name} -> Command: {command}")
        return f"Application launched successfully using shortcut '{name}'."
    except Exception as e:
        print(f"Failed to launch application using shortcut '{name}': {e}")
        return f"Failed to launch application using shortcut '{name}': {e}"



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
                print(f"Shortcut: {name} -> Command: {command}")
    
    elif choice == "2":
        name = input("Enter shortcut name: ")
        command = input("Enter command to launch: ")
        result = add_shortcut(name, command)
        print(result)
    
    elif choice == "3":
        name = input("Enter shortcut name to remove: ")
        result = remove_shortcut(name)
        print(result)
    
    elif choice == "4":
        name = input("Enter shortcut name to launch: ")
        result = launch_shortcut(name)
        print(result)
    
    elif choice == "5":
        print("Exiting Launch Shortcuts Management.")
        break
    
    else:
        print("Invalid choice. Please try again.")