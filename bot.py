import os
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting with interactive buttons."""
    user = update.effective_user
    
    keyboard = [
        [
            InlineKeyboardButton("📜 About Me", callback_data='about'),
            InlineKeyboardButton("🛠 Features", callback_data='features'),
        ],
        [InlineKeyboardButton("🎁 Surprise Me!", callback_data='surprise')],
        [InlineKeyboardButton("🌐 Support Website", url='https://github.com/HerixH/HarperTheBot')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n\nI'm **Harper**, your premium interactive assistant.\n"
        "I'm now running live on Railway! 🚀\n\n"
        "What would you like to do?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == 'about':
        await query.edit_message_text(
            text="✨ *About Harper*\n\nI am a specialized Telegram bot designed for high-performance interactions. "
                 "Built with Python and hosted on Railway's cloud infrastructure.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'features':
        await query.edit_message_text(
            text="🚀 *My Current Features*\n\n"
                 "• Interactive Menus\n"
                 "• Real-time Echoing\n"
                 "• Cloud Connectivity\n"
                 "• Fast Latency\n\n_More coming soon!_",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'surprise':
        surprises = [
            "🌟 Did you know? Railway is awesome for hosting bots!",
            "🤖 I was born just today and I'm already learning so much!",
            "⚡ I can process messages in milliseconds!",
            "🍀 You're having a great day? I hope so!",
            "🎨 Customization is my middle name. (Actually it's 'The')"
        ]
        await query.edit_message_text(
            text=f"🎁 *Surprise!*\n\n{random.choice(surprises)}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'back_to_start':
        # Re-show the original start menu
        keyboard = [
            [
                InlineKeyboardButton("📜 About Me", callback_data='about'),
                InlineKeyboardButton("🛠 Features", callback_data='features'),
            ],
            [InlineKeyboardButton("🎁 Surprise Me!", callback_data='surprise')],
            [InlineKeyboardButton("🌐 Support Website", url='https://github.com/HerixH/HarperTheBot')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"Main Menu\n\nWhat would you like to do?",
            reply_markup=reply_markup
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echoes the user message with a bit of style."""
    text = update.message.text
    await update.message.reply_text(f"📝 *You said:* \n_{text}_", parse_mode='Markdown')

if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    
    if not TOKEN:
        print("Error: No BOT_TOKEN found in environment variables.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    
    print("Harper is now live and interactive!")
    application.run_polling()
