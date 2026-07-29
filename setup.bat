@echo off
echo Setting up CtrlRelay...
pip install -r requirements.txt
echo.
echo Setup complete! Next steps:
echo 1. Edit .env file with your Telegram bot token and allowed chat IDs
echo 2. Configure launch shortcuts in configs/launch/launch.json (optional)
echo 3. Run main.py to start the bot
pause