import os
import logging
import random
import asyncio
import httpx  # For fetching news
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from duckduckgo_search import DDGS

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting with the highly visible Blockchain menu."""
    user = update.effective_user
    
    # Force keyboard to be visible and add a placeholder
    reply_keyboard = [
        ['🔗 Blockchain News', '💰 Crypto Prices'],
        ['🎮 Play Games', '📊 Daily Poll'],
        ['👋 Say Hello', '⚙️ Settings']
    ]
    markup = ReplyKeyboardMarkup(
        reply_keyboard, 
        resize_keyboard=True, 
        input_field_placeholder="Select a blockchain feature..."
    )

    inline_keyboard = [
        [
            InlineKeyboardButton("📰 Latest News", callback_data='news'),
            InlineKeyboardButton("📊 Market Stats", callback_data='stats'),
        ],
        [InlineKeyboardButton("🎉 Ultimate Surprise", callback_data='surprise')],
        [InlineKeyboardButton("🔗 GitHub Repo", url='https://github.com/HerixH/HarperTheBot')],
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(
        f"🏆 *Welcome to Harper v3.6, {user.first_name}!*\n\n"
        "Your **Blockchain Assistant** is ready. 🌐\n\n"
        "Buttons should now appear at the bottom of your screen. If not, tap the [::] icon in your chat bar!",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "✨ *Market Dashboard:*",
        reply_markup=inline_markup,
        parse_mode='Markdown'
    )

async def blockchain_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Direct command to open the blockchain menu."""
    await start(update, context)

async def fetch_blockchain_news():
    """Fetches real blockchain news from CryptoCompare."""
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            news_items = []
            for item in data.get('Data', [])[:3]:
                news_items.append({
                    "t": item.get('title', 'No Title'),
                    "d": item.get('body', 'No Description')[:200] + "..."
                })
            if not news_items:
                raise Exception("Empty news data")
            return news_items
    except Exception as e:
        logging.error(f"Error fetching news: {e}")
        return [
            {"t": "Bitcoin Stability", "d": "BTC remains strong as institutional interest grows in the current market cycle."},
            {"t": "Ethereum Ecosystem", "d": "The Ethereum network continues to lead in decentralization and smart contract innovation."},
            {"t": "Web3 Future", "d": "New developments in Web3 are bridging the gap between traditional tech and decentralized finance."}
        ]

async def fetch_crypto_prices():
    """Fetches real market prices from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin,ripple,cardano&vs_currencies=usd&include_24hr_change=true"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            data = response.json()
            
            mapping = {
                "bitcoin": ("BTC", "₿"),
                "ethereum": ("ETH", "💎"),
                "solana": ("SOL", "⚡"),
                "binancecoin": ("BNB", "🔶"),
                "ripple": ("XRP", "💧"),
                "cardano": ("ADA", "🔵")
            }
            
            prices_text = "💰 *Harper Market Hub (Live)*\n\n"
            for coin_id, (symbol, emoji) in mapping.items():
                if coin_id in data:
                    price = data[coin_id]['usd']
                    change = data[coin_id].get('usd_24h_change', 0)
                    change_str = f"{change:+.2f}%"
                    indicator = "📈" if change >= 0 else "📉"
                    prices_text += f"{emoji} *{symbol}:* ${price:,.2f} ({change_str} {indicator})\n"
            
            prices_text += "\n_Source: CoinGecko Live-Feed_"
            return prices_text
    except Exception as e:
        logging.error(f"Error fetching prices: {e}")
        return "⚠️ *Error fetching live prices.*\n\nPlease try again later."

async def search_internet(query):
    """Searches the internet for general queries when keywords aren't met."""
    def _search():
        try:
            from datetime import datetime
            current_year = datetime.now().year
            # Append current year for relevancy
            refined_query = f"{query} {current_year}" if str(current_year) not in query else query
            # Force English results with english-only language filter
            refined_query = refined_query + " site:en"

            results = []
            with DDGS() as ddgs:
                # region='en-us' enforces English-language results
                for r in ddgs.text(refined_query, region='en-us', max_results=3, timelimit='m'):
                    title = r['title']
                    body = r['body']
                    if len(body) > 300:
                        body = body[:297] + "..."
                    results.append(f"🔹 *{title}*\n{body}\n")

            # Fallback: no timelimit, but still English
            if not results:
                for r in ddgs.text(query + f" {current_year}", region='en-us', max_results=3):
                    body = r['body'][:297] + "..."
                    results.append(f"🔹 *{r['title']}*\n{body}\n")

            return results
        except Exception as e:
            logging.error(f"Internet search error internal: {e}")
            return None

    try:
        results = await asyncio.to_thread(_search)
        if not results:
            return None

        return "🌐 *Harper Web Search (Live 2026):*\n\n" + "\n".join(results)
    except Exception as e:
        logging.error(f"Internet search error: {e}")
        return None

async def fetch_market_stats():
    """Fetches global market stats and Fear & Greed index."""
    try:
        async with httpx.AsyncClient() as client:
            # Global Stats
            global_resp = await client.get("https://api.coingecko.com/api/v3/global", timeout=10.0)
            global_data = global_resp.json().get('data', {})
            
            cap = global_data.get('total_market_cap', {}).get('usd', 0) / 1e12
            btc_dom = global_data.get('market_cap_percentage', {}).get('btc', 0)
            
            # Fear & Greed
            fng_resp = await client.get("https://api.alternative.me/fng/", timeout=10.0)
            fng_data = fng_resp.json().get('data', [{}])[0]
            fng_value = fng_data.get('value', '??')
            fng_text = fng_data.get('value_classification', 'Unknown')
            
            return (f"📊 *Blockchain Market Sentiment*\n\n"
                    f"• *Fear & Greed Index:* {fng_value} ({fng_text}) 🎭\n"
                    f"• *BTC Dominance:* {btc_dom:.1f}%\n"
                    f"• *Global Market Cap:* ${cap:.2f}T\n\n_"
                    f"Data fetched live from Harper Network._")
    except Exception as e:
        logging.error(f"Error fetching stats: {e}")
        return "⚠️ *Error fetching live market stats.*"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles news and stats button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == 'news':
        news = await fetch_blockchain_news()
        news_text = "📰 *Latest Blockchain Headlines*\n\n"
        for item in news:
            news_text += f"🔹 *{item['t']}*\n_{item['d']}_\n\n"
        
        await query.edit_message_text(
            text=news_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh News", callback_data='news')], [InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'stats':
        stats_text = await fetch_market_stats()
        await query.edit_message_text(
            text=stats_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh Stats", callback_data='stats')], [InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'surprise':
        await query.edit_message_text(text="🎯 Watch this! I'm sending a lucky dice in 3... 2... 1...")
        await asyncio.sleep(2)
        await context.bot.send_dice(chat_id=query.message.chat_id, emoji="🎲")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Did you get a 6? If so, you're officially lucky! 🍀",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]])
        )
    elif query.data == 'back_to_start':
        inline_keyboard = [
            [
                InlineKeyboardButton("📰 Latest News", callback_data='news'),
                InlineKeyboardButton("📊 Market Stats", callback_data='stats'),
            ],
            [InlineKeyboardButton("🎉 Ultimate Surprise", callback_data='surprise')],
            [InlineKeyboardButton("💎 Support Repository", url='https://github.com/HerixH/HarperTheBot')],
        ]
        await query.edit_message_text(
            text="Main Menu Refreshed! ✨\n\nChoose an action:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard)
        )

async def handle_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles both menu buttons AND flexible keyword detection."""
    import re
    text = update.message.text
    text_lower = text.lower()

    def has_word(word):
        return bool(re.search(rf"\b{re.escape(word)}\b", text_lower))

    # --- Knowledge Base ---
    knowledge = {
        "vitalik": "💎 **Vitalik Buterin** is the co-founder of Ethereum. He's a visionary focused on blockchain scalability and decentralization.",
        "satoshi": "🪙 **Satoshi Nakamoto** is the pseudonymous creator of Bitcoin. The whitepaper released in 2008 started the entire crypto revolution!",
        "herix": "👨‍💻 **Herix** is the main developer and architect of Harper Bot. He's dedicated to building specialized AI tools for the Web3 community.",
        "solana": "⚡ **Solana (SOL)** is a high-speed, high-performance blockchain known for its fast transactions and low costs.",
        "ethereum": "🌐 **Ethereum (ETH)** is the world's leading smart-contract platform, powering DeFi, NFTs, and decentralized apps.",
        "bitcoin": "🥇 **Bitcoin (BTC)** is the first and most secure cryptocurrency, often regarded as 'Digital Gold'.",
        "harper": "🤖 That's me! I'm **Harper**, your AI Blockchain Assistant. I'm here to help you navigate the world of decentralized finance!",
    }

    # --- Single unified if/elif/else chain ---

    if "my name is " in text_lower:
        new_name = text.split("is", 1)[1].strip()
        context.user_data['custom_name'] = new_name
        await update.message.reply_text(f"👋 Nice to meet you, **{new_name}**! I'll remember that. Ask me 'What's my name' anytime!", parse_mode='Markdown')

    elif "what is my name" in text_lower or "what's my name" in text_lower:
        saved_name = context.user_data.get('custom_name', update.effective_user.first_name)
        await update.message.reply_text(f"👤 Your name is **{saved_name}**! It's a pleasure to assist you.", parse_mode='Markdown')

    elif "who are you" in text_lower or "your name" in text_lower:
        await update.message.reply_text("🤖 I am **Harper**, your premium AI assistant, running live on Railway! 🚀", parse_mode='Markdown')

    elif any(has_word(k) for k in ["news", "blockchain", "headlines"]):
        news = await fetch_blockchain_news()
        await update.message.reply_text("🔎 Fetching the latest blocks...")
        await asyncio.sleep(1)
        news_text = "🗞 *Harper Blockchain Feed*\n\n"
        for item in news:
            news_text += f"🔥 *{item['t']}*\n_{item['d']}_\n\n"
        await update.message.reply_text(news_text, parse_mode='Markdown')

    elif any(has_word(k) for k in ["price", "crypto", "market", "ticker"]):
        await update.message.reply_text("💹 Loading live market data...")
        prices = await fetch_crypto_prices()
        await update.message.reply_text(prices, parse_mode='Markdown')

    elif any(has_word(k) for k in ["game", "play", "lucky", "dice"]):
        await update.message.reply_text("Feeling lucky? Choose your game:")
        await update.message.reply_dice(emoji="🎰")

    elif any(has_word(k) for k in ["poll", "vote", "daily"]):
        questions = ["Which chain is better?", "HODL or Trade?", "Is Web3 the future?"]
        options = [["Solana", "Ethereum", "Bitcoin"], ["HODL 💎", "Trade 📉"], ["Yes! ✅", "Not sure 🧐"]]
        idx = random.randint(0, len(questions)-1)
        await context.bot.send_poll(update.effective_chat.id, questions[idx], options[idx], is_anonymous=False)

    elif any(has_word(k) for k in ["hello", "hi", "hey", "greet", "sup", "yo"]):
        await update.message.reply_text(f"Hello {update.effective_user.first_name}! Ready to explore the blockchain? 🚀")

    elif any(has_word(k) for k in ["yes", "yeah", "yep", "sure", "ok", "okay", "alright", "yup", "nope", "no", "nah", "thanks", "thank", "cool", "great", "nice"]):
        responses = [
            f"Got it, {update.effective_user.first_name}! 😊 What would you like to explore? Try **news**, **prices**, or ask me anything!",
            f"Awesome! 🚀 Use the menu below or type **'prices'** to see live crypto rates!",
            f"Roger that! 👍 What's on your mind? Try asking about **Bitcoin**, **Ethereum**, or **news**!",
        ]
        await update.message.reply_text(random.choice(responses), parse_mode='Markdown')

    elif any(has_word(k) for k in ["joke"]):
        jokes = ["Why did the crypto trader cross the road? To get to the other side of the pump!", "Blockchain is like a relationship: once it's committed, you can't change the history."]
        await update.message.reply_text(random.choice(jokes))

    elif has_word("time"):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        await update.message.reply_text(f"🕒 The current server time is: **{now}**", parse_mode='Markdown')

    elif has_word("opencl"):
        await update.message.reply_text(
            "🦞 *OpenClaw Features*\n\n"
            "OpenClaw is an advanced automation framework. Features include:\n"
            "• **Stealth Browsing:** Bypasses bot detection.\n"
            "• **Multi-Agent Orchestration:** Run tasks across AI nodes.\n"
            "• **Data Extraction:** Structured APIs from any site.\n",
            parse_mode='Markdown'
        )

    elif any(key in text_lower for key in knowledge):
        for key, info in knowledge.items():
            if key in text_lower:
                await update.message.reply_text(f"📚 *Harper Knowledge:* \n\n{info}", parse_mode='Markdown')
                break

    else:
        # Only do internet search for meaningful queries (length > 3 chars)
        if len(text.strip()) <= 3:
            await update.message.reply_text(
                f"🤖 Not sure what you mean by *{text}*! Try saying **'prices'**, **'news'**, or ask me anything about crypto!",
                parse_mode='Markdown'
            )
            return

        # Internet search fallback — only runs when nothing else matched
        await update.message.reply_chat_action("typing")
        search_results = await search_internet(text)

        if search_results:
            await update.message.reply_text(search_results, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                f"🎯 *Harper v3.7*\n\nI couldn't find info on _{text}_ right now.\n\n"
                "Try asking about **prices**, **news**, or specific crypto like **Solana**!",
                parse_mode='Markdown'
            )

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets new members when they join a group."""
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("Thanks for adding me! I'm Harper, your Blockchain Assistant. Type /start to see what I can do!")
        else:
            await update.message.reply_text(
                f"Welcome {member.first_name} to the group! 🎉\n"
                "I am Harper, the community bot. Check out my blockchain features by typing /start!"
            )

if __name__ == '__main__':
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        print("Error: No BOT_TOKEN found in environment variables.")
        exit(1)

    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('blockchain', blockchain_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_replies))
    
    print("Harper v3.6 is live with Personalized Features & Knowledge Base!")
    application.run_polling()

