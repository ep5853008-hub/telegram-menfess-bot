import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_FOR_MESSAGE = 1
WAITING_FOR_CONFIRM = 2

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TARGET_CHANNEL = os.environ.get("TARGET_CHANNEL", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    text = (
        f"Halo {user.first_name}! 👋\n\n"
        "Kirim menfess anonim kamu:\n\n"
        "Format bebas, langsung ketik pesanmu."
    )
    await update.message.reply_text(text)
    return WAITING_FOR_MESSAGE


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message.text

    if len(msg) > 1000:
        await update.message.reply_text("⚠️ Maksimal 1000 karakter.")
        return WAITING_FOR_MESSAGE

    context.user_data["msg"] = msg

    keyboard = [
        [
            InlineKeyboardButton("✅ Kirim", callback_data="send"),
            InlineKeyboardButton("❌ Batal", callback_data="cancel"),
        ]
    ]

    await update.message.reply_text(
        f"Preview:\n\n{msg}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return WAITING_FOR_CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    msg = context.user_data.get("msg", "")

    if TARGET_CHANNEL:
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL,
            text=f"📨 Menfess:\n\n{msg}"
        )
        await query.edit_message_text("✅ Terkirim!")
    else:
        await query.edit_message_text("⚠️ TARGET_CHANNEL belum diset.")

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Dibatalkan.")
    context.user_data.clear()
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)
            ],
            WAITING_FOR_CONFIRM: [
                CallbackQueryHandler(confirm, pattern="^send$"),
                CallbackQueryHandler(cancel, pattern="^cancel$"),
            ],
        },
        fallbacks=[],
    )

    app.add_handler(conv)

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
