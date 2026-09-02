@echo off
pyinstaller --onefile  --add-data "configs/launch/launch.json;configs/launch" --add-data "requirements.txt;." --hidden-import=win32timezone --hidden-import=pkgutil --hidden-import=handlers.manager --hidden-import=handlers.power --hidden-import=handlers.utility --exclude-module PyQt5 --exclude-module PySide6 --collect-all handlers --collect-all modules --collect-all bot_utils main.py  --add-data "icons;icons" --icon CtrlRelay.ico --name CtrlRelay


::: --add-data ".env;."