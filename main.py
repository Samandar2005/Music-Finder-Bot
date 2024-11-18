from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database import initialize_database
from handlers import start, handle_message, statistics, download_mp3
from dotenv import load_dotenv
import os


def main():
    """Botni ishga tushirish."""
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("Bot token not found in .env file")

    initialize_database()

    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("statistics", statistics))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(download_mp3))

    application.run_polling()


if __name__ == "__main__":
    main()
