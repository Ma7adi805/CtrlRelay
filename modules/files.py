import os, sys
from pathlib import Path

from core import settings
from core.settings import reload_settings


def _isvalid_path(path: str) -> bool:
    """Check if the given path is valid and allowed."""
    reload_settings()
    path = path.strip().replace("/", "\\") 
    
    norm_path = os.path.normpath(path)
    for allowed_path in settings.ALLOWED_PATHS:
        allowed_path = allowed_path.replace("%USERPROFILE%", os.path.expanduser("~"))
        norm_allowed = os.path.normpath(allowed_path)
        if norm_path.startswith(norm_allowed):
            return True
    for allowed_path in settings.DOWNLOAD_PATH:
        allowed_path = allowed_path.replace("%USERPROFILE%", os.path.expanduser("~"))
        norm_allowed = os.path.normpath(allowed_path)
        if norm_path.startswith(norm_allowed):
            return True
    return False


def crop_file_path(file_path:str) -> tuple[str, bool]:
    """
    Crop the file path to show only the last two segments.
    For example, "C:/Users/Public/Downloads/CtrlRelay/file.txt" becomes "Downloads/CtrlRelay/file.txt"
    Returns a tuple of (cropped_path, is_valid) where is_valid indicates if the path is valid in .env.
    """
    valid = False
    parts = file_path.replace("\\", "/").split("/")
    parts = "/".join(parts[-3:])  # always a string, never a list
    valid = _isvalid_path(file_path)

    return parts, valid

def uncrop_file_path(cropped_path: str) -> tuple[str, bool]:
    reload_settings()
    cropped_normalized = cropped_path.strip().replace("/", "\\").strip("\\")
    cropped_segments = cropped_normalized.split("\\")

    for allowed_path in settings.ALLOWED_PATHS + settings.DOWNLOAD_PATH:
        allowed_path = allowed_path.replace("%USERPROFILE%", os.path.expanduser("~"))
        allowed_normalized = allowed_path.replace("/", "\\")
        allowed_segments = allowed_normalized.split("\\")
        # Check if cropped is a suffix of this allowed path
        if len(cropped_segments) <= len(allowed_segments):
            tail = allowed_segments[-len(cropped_segments):]
            if tail == cropped_segments:
                return allowed_path, _isvalid_path(allowed_path)

        # Fallback: append cropped to allowed path, check existence
        candidate = os.path.join(allowed_path, cropped_normalized)
        if os.path.exists(candidate):
            return candidate, _isvalid_path(candidate)

    return cropped_path, False

def list_directory_contents(path: str) -> tuple[list[str], Exception | None]:
    """List the contents of a directory."""
    path = path.strip().replace("/", "\\")  # Normalize path separators
    try:
        if not _isvalid_path(path):
            raise PermissionError(f"Access to the path '{path}' is not allowed.")
        contents = os.listdir(path)
        return contents, None
    except Exception as e:
        return [], e