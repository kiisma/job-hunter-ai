"""Entry point for the Telegram shipping-calculator bot."""
import logging

from telegram_bot.bot import create_app

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

if __name__ == "__main__":
    app = create_app()
    app.run_polling(drop_pending_updates=True)
