import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting message when the command /start is issued."""
    await update.message.reply_text(
        f"Hello {update.effective_user.first_name}! I am Harper The Bot. 🤖\n\n"
        "I'm currently running on Railway. How can I help you today?"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echoes the user message."""
    await update.message.reply_text(f"You said: {update.message.text}")

if __name__ == '__main__':
    # Get token from environment variable (Best practice for Railway)
    TOKEN = os.environ.get("BOT_TOKEN")
    
    if not TOKEN:
        print("Error: No BOT_TOKEN found in environment variables.")
        exit(1)

    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    
    # Start the bot
    print("Harper The Bot is starting...")
    application.run_polling()
