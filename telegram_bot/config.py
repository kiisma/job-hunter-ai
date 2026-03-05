import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPERATOR_CHAT_ID: int = int(os.getenv("OPERATOR_CHAT_ID", "0"))

# Business logic constants
RUSSIA_SHIPPING_PER_KG: float = float(os.getenv("RUSSIA_SHIPPING_PER_KG", "15"))  # EUR per kg
MARKUP_PERCENT: float = float(os.getenv("MARKUP_PERCENT", "25"))  # %
