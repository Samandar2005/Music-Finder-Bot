from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database import initialize_database
from handlers import start, handle_message, statistics

def main():
    """Botni ishga tushirish."""
    initialize_database()

    application = Application.builder().token("7573018273:AAH8_XtkleOY566-VJ8jsZipgLOTpGQBwvI").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("statistics", statistics))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()


if __name__ == "__main__":
    main()
