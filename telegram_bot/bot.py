"""
Telegram bot for calculating shipping costs to Russia via Portugal.

Conversation flow
-----------------
/start
  → WAITING_LINK   : ask for product URL
  → handle_link    : scrape URL, show item card
  → WAITING_MORE   : [Да, ещё товар] / [Нет, это всё]
      ↳ add_more   → WAITING_LINK (loop)
      ↳ done       → WAITING_CONFIRM : show order summary
  → handle_confirm / handle_cancel → END
"""
import logging
from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from .calculator import calculate_order
from .config import BOT_TOKEN, OPERATOR_CHAT_ID
from .models import OrderItem
from .scraper import scrape_product

logger = logging.getLogger(__name__)

# ── Conversation states ───────────────────────────────────────────────────────
WAITING_LINK = 1
WAITING_MORE = 2
WAITING_CONFIRM = 3

# ── Keyboard helpers ──────────────────────────────────────────────────────────

def _kb_add_more() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Да, ещё товар", callback_data="add_more"),
            InlineKeyboardButton("🛒 Нет, к оформлению", callback_data="done"),
        ]]
    )


def _kb_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("✅ Подтвердить заказ", callback_data="confirm"),
            InlineKeyboardButton("❌ Отмена", callback_data="cancel"),
        ]]
    )


# ── Formatting helpers ────────────────────────────────────────────────────────

def _fmt_item_card(item: OrderItem) -> str:
    p = item.product
    pt_ship = "Бесплатно" if p.shipping_to_portugal == 0 else f"{p.shipping_to_portugal:.2f} EUR"
    return (
        f"📦 *{_esc(p.name)}*\n"
        f"💰 Цена: {p.price:.2f} {p.currency}\n"
        f"⚖️ Примерный вес: {p.weight_kg:.2f} кг\n"
        f"🇵🇹 Доставка до Португалии: {pt_ship}"
    )


def _fmt_order_summary(items: List[OrderItem]) -> str:
    from .calculator import calculate_order  # local import to avoid circular
    summary = calculate_order(items)
    lines = ["📋 *Ваш заказ:*\n"]
    for idx, item in enumerate(summary.items, 1):
        p = item.product
        lines.append(
            f"*{idx}\\. {_esc(p.name)}*\n"
            f"   {p.price:.2f} {p.currency} × {item.quantity} шт\\."
        )
    lines.append("")
    lines.append(f"💵 Стоимость товаров: *{summary.total_product_cost:.2f} EUR*")
    lines.append(f"➕ Наценка \\(25%\\): {summary.markup_amount:.2f} EUR")
    lines.append(f"⚖️ Общий вес: \\~{summary.total_weight_kg:.2f} кг")
    lines.append(f"🚚 Доставка в Россию \\(\\~15 EUR/кг\\): {summary.russia_shipping:.2f} EUR")
    if summary.portugal_shipping > 0:
        lines.append(f"🇵🇹 Доставка до Португалии: {summary.portugal_shipping:.2f} EUR")
    lines.append(f"\n💶 *ИТОГО: {summary.grand_total:.2f} EUR*")
    lines.append("\n_Это приблизительная стоимость\\. Окончательная цена уточняется менеджером\\._")
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape special MarkdownV2 characters."""
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text


# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["items"] = []
    await update.message.reply_text(
        "👋 Привет\\! Я помогу рассчитать *примерную стоимость* доставки товаров из Португалии в Россию\\.\n\n"
        "Пришлите мне ссылку на первый товар:",
        parse_mode="MarkdownV2",
    )
    return WAITING_LINK


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    url = update.message.text.strip()

    if not url.startswith("http"):
        await update.message.reply_text(
            "⚠️ Пожалуйста, пришлите корректную ссылку \\(начинается с `http://` или `https://`\\)\\.",
            parse_mode="MarkdownV2",
        )
        return WAITING_LINK

    msg = await update.message.reply_text("⏳ Получаю информацию о товаре\\.\\.\\.", parse_mode="MarkdownV2")

    try:
        product = await scrape_product(url)
    except Exception as exc:
        logger.error("Scraping failed for %s: %s", url, exc)
        await msg.edit_text(
            "❌ Не удалось получить информацию о товаре\\. "
            "Проверьте ссылку и попробуйте ещё раз:",
            parse_mode="MarkdownV2",
        )
        return WAITING_LINK

    item = OrderItem(product=product, quantity=1)
    context.user_data.setdefault("items", []).append(item)

    await msg.edit_text(
        "✅ Товар добавлен\\!\n\n" + _fmt_item_card(item),
        parse_mode="MarkdownV2",
    )
    await update.message.reply_text(
        "Хотите добавить ещё один товар?",
        reply_markup=_kb_add_more(),
    )
    return WAITING_MORE


async def cb_add_more(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Пришлите ссылку на следующий товар:")
    return WAITING_LINK


async def cb_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    items: List[OrderItem] = context.user_data.get("items", [])
    if not items:
        await query.edit_message_text(
            "Список товаров пуст\\. Начните заново — /start",
            parse_mode="MarkdownV2",
        )
        return ConversationHandler.END

    summary_text = _fmt_order_summary(items)
    await query.edit_message_text(
        summary_text,
        parse_mode="MarkdownV2",
        reply_markup=_kb_confirm(),
    )
    return WAITING_CONFIRM


async def cb_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user = query.from_user
    items: List[OrderItem] = context.user_data.get("items", [])
    from .calculator import calculate_order
    summary = calculate_order(items)

    # ── Notify operator ───────────────────────────────────────────────────────
    if OPERATOR_CHAT_ID:
        username = f"@{user.username}" if user.username else f"ID: {user.id}"
        op_lines = [
            "🛒 *НОВЫЙ ЗАКАЗ*\n",
            f"👤 Клиент: {_esc(user.full_name)}",
            f"📱 {_esc(username)}",
            f"🆔 User ID: `{user.id}`\n",
            "📦 *Товары:*",
        ]
        for idx, item in enumerate(items, 1):
            p = item.product
            op_lines.append(
                f"{idx}\\. {_esc(p.name)}\n"
                f"   Цена: {p.price:.2f} {p.currency} × {item.quantity} шт\\.\n"
                f"   🔗 {_esc(p.url)}"
            )
        op_lines += [
            "",
            f"💵 Товары: {summary.total_product_cost:.2f} EUR",
            f"➕ Наценка: {summary.markup_amount:.2f} EUR",
            f"⚖️ Вес: \\~{summary.total_weight_kg:.2f} кг",
            f"🚚 Доставка РФ: {summary.russia_shipping:.2f} EUR",
            f"🇵🇹 Доставка PT: {summary.portugal_shipping:.2f} EUR",
            f"\n💶 *ИТОГО: {summary.grand_total:.2f} EUR*",
        ]
        try:
            await context.bot.send_message(
                chat_id=OPERATOR_CHAT_ID,
                text="\n".join(op_lines),
                parse_mode="MarkdownV2",
            )
        except Exception as exc:
            logger.error("Failed to notify operator: %s", exc)

    await query.edit_message_text(
        "✅ *Заказ принят\\!*\n\n"
        "Менеджер свяжется с вами в ближайшее время для подтверждения заказа "
        "и уточнения деталей оплаты и доставки\\.\n\n"
        "Спасибо за обращение\\! 🙏",
        parse_mode="MarkdownV2",
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cb_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "❌ Заказ отменён\\. Чтобы начать заново — /start",
        parse_mode="MarkdownV2",
    )
    return ConversationHandler.END


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Заказ отменён\\. Начните заново — /start",
        parse_mode="MarkdownV2",
    )
    return ConversationHandler.END


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            WAITING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link),
            ],
            WAITING_MORE: [
                CallbackQueryHandler(cb_add_more, pattern="^add_more$"),
                CallbackQueryHandler(cb_done, pattern="^done$"),
            ],
            WAITING_CONFIRM: [
                CallbackQueryHandler(cb_confirm, pattern="^confirm$"),
                CallbackQueryHandler(cb_cancel, pattern="^cancel$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,  # /start restarts from any state
    )

    app.add_handler(conv)
    return app
