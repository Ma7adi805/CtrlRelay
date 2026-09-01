<img src="CtrlRelay.png" alt="CtrlRelay Logo" width="100">

# CtrlRelay

A lightweight Windows utility that lets you control your PC remotely through a Telegram bot.

[![Pre-release](https://img.shields.io/badge/release-pre--release-yellow)](https://github.com/Ma7adi805/CtrlRelay/releases/latest)

## Features

1. Control your PC remotely via Telegram
2. Upload files through Telegram
3. Type and control your keyboard remotely
4. Manage everything from the system tray, no terminal needed
5. Additional functionality coming soon

## System Tray

CtrlRelay runs entirely from the system tray, no terminal window needed. Once launched, an icon appears in your taskbar notification area where you can manage the bot at any time.

| Menu Item | Description |
|-----------|-------------|
| Status | Shows the current state: Starting, Running, Stopping, Stopped, or Error. When in an error state, clicking it opens the log file. |
| Start | Starts the Telegram bot. Available when the bot is stopped or in an error state. |
| Restart | Restarts the bot. Available while it is running. |
| Stop | Gracefully stops the bot. |
| Open .env | Opens your configuration file in the default text editor. |
| Quit | Stops the bot and exits the application. |

Buttons are automatically enabled or disabled based on the current state, so you always know what actions are available.

## Getting Started

1. Visit the [releases](https://github.com/Ma7adi805/CtrlRelay/releases/latest) page.
2. Download the latest `.exe` file.
3. Run the executable. It will generate a `.env` configuration file and attempt to start the bot, then a tray icon will appear in your taskbar.
4. Open the `.env` file. You can find it in the same folder as the executable, or open it directly from the tray menu using **Open .env**.
5. Fill in your Telegram bot token and allowed chat ID, then save the file. To get your chat ID, send `/start` to your bot in Telegram first.
6. Press **Restart** in the tray menu. The bot will reload your settings and start running.

## Technologies Used

| Library | Purpose |
|---------|---------|
| Python | Core language |
| python-telegram-bot | Telegram bot API integration |
| pystray | System tray icon and menu |
| Pillow | Tray icon rendering |

## Contact

For questions, issues, or contributions, visit the [issue tracker](https://github.com/Ma7adi805/CtrlRelay/issues).

## License

This project is currently in pre-release. License details will be provided in an upcoming release.
