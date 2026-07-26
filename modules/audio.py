import sounddevice as sd
import platform, subprocess
import warnings

# Suppress pycaw COMError warnings from audio device enumeration
warnings.filterwarnings("ignore", category=UserWarning, module="pycaw.utils")

def get_clean_output_devices() -> list[dict]:
    """Get unique, modern audio output devices tailored to the host OS."""
    devices = sd.query_devices()
    host_apis = sd.query_hostapis()
    current_os = platform.system()
    
    # Target the best modern Sound Engine per Operating System
    target_api_keyword = "WASAPI"       # Windows
    if current_os == "Darwin":
        target_api_keyword = "Core Audio"  # macOS
    elif current_os == "Linux":
        target_api_keyword = "ALSA"        # Linux Base

    # Find the backend index
    target_api_idx = next((idx for idx, api in enumerate(host_apis) if target_api_keyword in api['name']), None)

    seen_names = set()
    clean_devices = []

    for index, device in enumerate(devices):
        if device['max_output_channels'] <= 0:
            continue
            
        # Isolate the target OS audio API layer
        if target_api_idx is not None and device['hostapi'] != target_api_idx:
            continue
            
        name = device['name']
        if "Hands-Free" in name or name.strip() == "Headphones ()":
            continue

        if name not in seen_names:
            seen_names.add(name)
            device_info = device.copy()
            device_info['original_index'] = index
            clean_devices.append(device_info)
            
    return clean_devices

def get_default_output_device() -> dict:
    """Get the active default output device on any operating system."""
    try:
        system_default_device = sd.query_devices(kind='output')
        default_name = system_default_device['name']
    except Exception:
        return None
        
    clean_devices = get_clean_output_devices()
    
    for device in clean_devices:
        if device['name'] == default_name or default_name in device['name'] or device['name'] in default_name:
            return device
            
    return None



def set_default_output_device(device_name: str) -> str:
    """
    Set the system default output audio device.
    Supports Windows, macOS, and Linux.
    """

    current_os = platform.system()

    try:
        # ================= WINDOWS =================
        if current_os == "Windows":
            import comtypes

            from pycaw.pycaw import AudioUtilities
            from pycaw.constants import ERole

            # Get all playback devices
            devices = AudioUtilities.GetAllDevices()

            target_device = None

            for device in devices:
                name = device.FriendlyName

                #print(f"Found: {name}")

                if name is None:
                    continue

                if device_name.lower() in name.lower():
                    target_device = device
                    break

            if not target_device:
                return f"❌ Could not find audio device: {device_name}"

            # Newer Pycaw method
            AudioUtilities.SetDefaultDevice(
                target_device.id,
                roles=[
                    ERole.eConsole,
                    ERole.eMultimedia,
                    ERole.eCommunications
                ]
            )

            return f"✅ Default output device set to {target_device.FriendlyName}"
        # ================= MACOS =================
        elif current_os == "Darwin":
            subprocess.run(
                [
                    "SwitchAudioSource",
                    "-s",
                    device_name
                ],
                check=True
            )

            return f"✅ Default output device set to {device_name}"
        # ================= LINUX =================
        elif current_os == "Linux":
            subprocess.run(
                [
                    "pactl",
                    "set-default-sink",
                    device_name
                ],
                check=True
            )
            return f"✅ Default output device set to {device_name}"
        else:
            return f"❌ Unsupported OS: {current_os}"
    except Exception as e:
        return f"❌ Failed to set default device: {e}"
    

def set_default_output_device_by_id(device_id: str) -> str:
    """
    Set the default output audio device using its Windows device ID.
    """

    current_os = platform.system()

    try:
        if current_os == "Windows":
            import comtypes

            from pycaw.pycaw import AudioUtilities
            from pycaw.constants import ERole

            devices = AudioUtilities.GetAllDevices()

            target_device = None

            for device in devices:
                if device.id == device_id:
                    target_device = device
                    break

            if not target_device:
                return f"❌ Could not find device ID: {device_id}"

            AudioUtilities.SetDefaultDevice(
                target_device.id,
                roles=[
                    ERole.eConsole,
                    ERole.eMultimedia,
                    ERole.eCommunications
                ]
            )

            return f"✅ Default output device set to {target_device.FriendlyName}"


        elif current_os == "Darwin":
            return "❌ Device IDs are not supported for macOS in this function."


        elif current_os == "Linux":
            subprocess.run(
                [
                    "pactl",
                    "set-default-sink",
                    device_id
                ],
                check=True
            )

            return f"✅ Default output device set to {device_id}"


        else:
            return f"❌ Unsupported OS: {current_os}"


    except Exception as e:
        return f"❌ Failed to set device: {e}"

def set_audio_volume(volume: int) -> str:
    """
    Set the system audio volume.
    Volume should be a float between 0 and 100
    """

    current_os = platform.system()

    try:
        if current_os == "Windows":
            from pycaw.pycaw import AudioUtilities

            device = AudioUtilities.GetSpeakers()
            device.EndpointVolume.SetMasterVolumeLevelScalar(volume / 100.0, None)

            return f"✅ Volume set to {volume}%"

        elif current_os == "Darwin":
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f"set volume output volume {volume}"
                ],
                check=True
            )
            return f"✅ Volume set to {volume}%"

        elif current_os == "Linux":
            subprocess.run(
                [
                    "pactl",
                    "set-sink-volume",
                    "@DEFAULT_SINK@",
                    f"{volume}%"
                ],
                check=True
            )
            return f"✅ Volume set to {volume}%"

        else:
            return f"❌ Unsupported OS: {current_os}"

    except Exception as e:
        return f"❌ Failed to set volume: {e}"

def get_audio_volume() -> int | None:
    """
    Get the current system audio volume.
    Returns an integer between 0 and 100, or None if it cannot be determined.
    """

    current_os = platform.system()

    try:
        if current_os == "Windows":
            from pycaw.pycaw import AudioUtilities

            device = AudioUtilities.GetSpeakers()
            volume = device.EndpointVolume.GetMasterVolumeLevelScalar() * 100
            return int(volume)

        elif current_os == "Darwin":
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    "output volume of (get volume settings)"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            return int(result.stdout.strip())

        elif current_os == "Linux":
            result = subprocess.run(
                [
                    "pactl",
                    "get-sink-volume",
                    "@DEFAULT_SINK@"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            # Example output: "Volume: front-left: 65536 / 100% / 0.00 dB,   front-right: 65536 / 100% / 0.00 dB"
            for part in result.stdout.split():
                if "%" in part:
                    return int(part.replace("%", ""))

        else:
            return None

    except Exception:
        return None


def mute_audio() -> str:
    """
    Mute the system audio.
    """

    current_os = platform.system()

    try:
        if current_os == "Windows":
            from pycaw.pycaw import AudioUtilities

            device = AudioUtilities.GetSpeakers()
            device.EndpointVolume.SetMute(1, None)

            return "✅ Audio muted"

        elif current_os == "Darwin":
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    "set volume output muted true"
                ],
                check=True
            )
            return "✅ Audio muted"

        elif current_os == "Linux":
            subprocess.run(
                [
                    "pactl",
                    "set-sink-mute",
                    "@DEFAULT_SINK@",
                    "1"
                ],
                check=True
            )
            return "✅ Audio muted"

        else:
            return f"❌ Unsupported OS: {current_os}"

    except Exception as e:
        return f"❌ Failed to mute audio: {e}"
        

def unmute_audio() -> str:
    """
    Unmute the system audio.
    """

    current_os = platform.system()

    try:
        if current_os == "Windows":
            from pycaw.pycaw import AudioUtilities

            device = AudioUtilities.GetSpeakers()
            device.EndpointVolume.SetMute(0, None)

            return "✅ Audio unmuted"

        elif current_os == "Darwin":
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    "set volume output muted false"
                ],
                check=True
            )
            return "✅ Audio unmuted"

        elif current_os == "Linux":
            subprocess.run(
                [
                    "pactl",
                    "set-sink-mute",
                    "@DEFAULT_SINK@",
                    "0"
                ],
                check=True
            )
            return "✅ Audio unmuted"

        else:
            return f"❌ Unsupported OS: {current_os}"

    except Exception as e:
        return f"❌ Failed to unmute audio: {e}"


"""
print("Available Output Audio Devices:")
for device in get_clean_output_devices():
    print(f"ID: {device['original_index']}, Name: {device['name']}")
print("\nDefault Output Device:")
default_device = get_default_output_device()
if default_device:
    print(f"ID: {default_device['original_index']}, Name: {default_device['name']}")
else:
    print("Default output device not found.")"""