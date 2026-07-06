##-----Libraries-----##
from tracemalloc import start
from flask import app
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from core.auth import restricted
from handlers.manager import ManagerHandler
from utils.logger import logger
from core.settings import BOT_TOKEN
import handlers.power as power
from handlers.power import PowerManagerCmd
#-----Setup-----##





async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id
    await update.message.reply_text(f"This is your chat ID: *{chat_id}*\n\nPlease add this ID to the ALLOWED\\_CHAT\\_IDS in the \\.env file to allow access\\.", parse_mode=ParseMode.MARKDOWN_V2)



async def onButtonClick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help_power":
        await PowerManagerCmd.help_power_command(update, context)


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Power Commands", callback_data="help_power")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What help do you need with?", reply_markup=reply_markup)
    

async def on_ready(application: ApplicationBuilder):
    logger.info(f"Bot is ready and running as: {application.bot.username}.")




def main():
    TOKEN = BOT_TOKEN
    if not TOKEN:
        logger.error("TELEGRAM_TOKEN is not set in the environment variables.")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(on_ready).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("power_off", PowerManagerCmd.power_off))
    app.add_handler(CommandHandler("abort_shutdown", PowerManagerCmd.abort_shutdown))
    app.add_handler(CommandHandler("restart", PowerManagerCmd.restart))
    app.add_handler(CommandHandler("abort_restart", PowerManagerCmd.abort_restart))
    app.add_handler(CommandHandler("get_uptime", PowerManagerCmd.get_uptime))
    app.add_handler(CommandHandler("sleep", PowerManagerCmd.sleep))
    app.add_handler(CommandHandler("hibernate", PowerManagerCmd.hibernate))
    app.add_handler(CommandHandler("abort_hibernate", PowerManagerCmd.abort_hibernate))
    app.add_handler(CommandHandler("help_power", PowerManagerCmd.help_power_command))
    app.add_handler(CommandHandler("lock", PowerManagerCmd.lock_system))
    app.add_handler(CallbackQueryHandler(onButtonClick))
    app.add_handler(CommandHandler("screenshot", ManagerHandler.screenshot))
    app.add_handler(CommandHandler("sysinfo", ManagerHandler.sysinfo))
    app.run_polling()

if __name__ == "__main__":
    main()