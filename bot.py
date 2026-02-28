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

def get_user_display_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    custom = context.user_data.get("custom_name")
    return custom if custom else update.effective_user.first_name

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a greeting with a premium banner and a refined menu layout."""
    user = update.effective_user
    user_name = get_user_display_name(update, context)
    
    # Path to the premium banner we generated
    banner_path = r'C:\Users\User\.gemini\antigravity\brain\119c2985-4be6-4a98-9d62-4c8695e691a1\harper_bot_banner_1772269612755.png'
    
    # Refined Keyboard Layout - Grouped for better UX
    reply_keyboard = [
        ['🗞 Latest News', '📈 Market Prices'],
        ['🕹 Play Games', '🗳 Daily Poll'],
        ['👤 My Profile', '⚙️ Bot Settings']
    ]
    markup = ReplyKeyboardMarkup(
        reply_keyboard, 
        resize_keyboard=True, 
        input_field_placeholder="Explore the blockchain hub..."
    )

    # 1. Send the Premium Banner as the single point of entry
    if os.path.exists(banner_path):
        await update.message.reply_photo(
            photo=open(banner_path, 'rb'),
            caption=(
                f"💎 *Welcome to Harper v3.8, {user_name}!* 💎\n\n"
                "I am your premium **AI Blockchain Assistant**, designed for speed, precision, and market insight. 🌐\n\n"
                "Use the menu below to navigate or ask me anything directly."
            ),
            reply_markup=markup,
            parse_mode='Markdown'
        )
    else:
        # Fallback if image isn't found
        await update.message.reply_text(
            f"🏆 *Welcome to Harper v3.8, {user_name}!*\n\n"
            "Your **Blockchain Assistant** is ready. 🌐\n\n"
            "The premium hub is now active. Explore below!",
            reply_markup=markup,
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
                InlineKeyboardButton("🗞 Headlines", callback_data='news'),
                InlineKeyboardButton("📊 Analytics", callback_data='stats'),
            ],
            [InlineKeyboardButton("🎲 Lucky Roll", callback_data='surprise')],
            [InlineKeyboardButton("💎 GitHub Project", url='https://github.com/HerixH/HarperTheBot')],
        ]
        await query.edit_message_text(
            text="*Main Menu Refreshed!* ✨\n\nChoose an action:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard),
            parse_mode='Markdown'
        )
    
    # --- Settings Callbacks ---
    elif query.data == 'rename_flow':
        await query.edit_message_text(
            text="✏️ *How to Rename*\n\nTo change your display name, simply type:\n`My name is [your name]`\n\nExample: `My name is Satoshi`",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'alerts_soon':
        await query.answer("🔔 Feature in development!")
        await query.edit_message_text(
            text="🚀 *Price Alerts*\n\nThis feature is coming in v4.0. You'll be able to set custom price triggers for BTC, ETH, and more!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='back_to_start')]]),
            parse_mode='Markdown'
        )
    elif query.data == 'reset_data':
        context.user_data.clear()
        await query.answer("🗑 Data cleared!")
        await query.edit_message_text(
            text="✅ *Data Reset*\n\nYour preferences and custom name have been cleared. Type /start to begin fresh!",
            parse_mode='Markdown'
        )

async def handle_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles both menu buttons AND flexible keyword detection."""
    import re
    text = update.message.text
    text_lower = text.lower().strip()
    user_name = get_user_display_name(update, context)
    last_topic = context.user_data.get('last_topic')

    def has_word(word):
        return bool(re.search(rf"\b{re.escape(word)}\b", text_lower))

    # --- Crypto aliases & typo map (maps input → canonical knowledge key) ---
    crypto_aliases = {
        "eth": "ethereum", "etherum": "ethereum", "etherium": "ethereum", "ether": "ethereum",
        "btc": "bitcoin", "bitcon": "bitcoin", "bitcoins": "bitcoin",
        "sol": "solana", "slana": "solana",
        "bnb": "binance", "binance": "binance",
        "xrp": "ripple", "ripple": "ripple",
        "ada": "cardano", "cardano": "cardano",
    }

    # --- Knowledge Base ---
    knowledge = {
        "vitalik": "💎 **Vitalik Buterin** is the co-founder of Ethereum. He's a visionary focused on blockchain scalability and decentralization.",
        "satoshi": "🪙 **Satoshi Nakamoto** is the pseudonymous creator of Bitcoin. The whitepaper released in 2008 started the entire crypto revolution!",
        "herix": "👨‍💻 **Herix** is the main developer and architect of Harper Bot. He's dedicated to building specialized AI tools for the Web3 community.",
        "solana": "⚡ **Solana (SOL)** is a high-speed, high-performance blockchain known for its fast transactions and low costs.",
        "ethereum": "🌐 **Ethereum (ETH)** is the world's leading smart-contract platform, powering DeFi, NFTs, and decentralized apps.",
        "bitcoin": "🥇 **Bitcoin (BTC)** is the first and most secure cryptocurrency, often regarded as 'Digital Gold'.",
        "ripple": "💧 **XRP (Ripple)** is a digital payment protocol focused on fast, low-cost international money transfers.",
        "cardano": "🔵 **Cardano (ADA)** is a proof-of-stake blockchain built for sustainability and smart contracts.",
        "binance": "🔶 **BNB (Binance Coin)** is the native token of the Binance ecosystem, one of the largest crypto exchanges.",
        "harper": "🤖 That's me! I'm **Harper**, your AI Blockchain Assistant. I'm here to help you navigate the world of decentralized finance!",
    }

    # --- Single unified if/elif/else chain ---

    if "my name is " in text_lower:
        new_name = text.split("is", 1)[1].strip()
        context.user_data['custom_name'] = new_name
        await update.message.reply_text(f"👋 Nice to meet you, **{new_name}**! I'll remember that. Ask me 'What's my name' anytime!", parse_mode='Markdown')

    elif "what is my name" in text_lower or "what's my name" in text_lower:
        saved_name = get_user_display_name(update, context)
        await update.message.reply_text(f"👤 Your name is **{saved_name}**! It's a pleasure to assist you.", parse_mode='Markdown')

    elif "who are you" in text_lower or "your name" in text_lower:
        await update.message.reply_text("🤖 I am **Harper**, your premium AI assistant, running live on Railway! 🚀", parse_mode='Markdown')

    elif any(k in text_lower for k in ["what do you do", "what can you do", "help", "capabilities", "commands", "how do you work"]):
        context.user_data['last_topic'] = 'help'
        await update.message.reply_text(
            f"🤖 *Here's what I can do, {user_name}:*\n\n"
            "📰 **Blockchain News** — Type *'news'* for live headlines\n"
            "💰 **Live Crypto Prices** — Type *'prices'* for BTC, ETH, SOL & more\n"
            "📊 **Market Stats** — Tap *Market Stats* in the menu\n"
            "🎲 **Games** — Type *'dice'* or *'game'*\n"
            "📚 **Crypto Knowledge** — Ask about Bitcoin, Ethereum, Solana, Vitalik...\n"
            "🌐 **Internet Search** — Ask me anything else and I'll search the web!\n\n"
            "_Tap /start to open the full menu!_",
            parse_mode='Markdown'
        )

    elif any(phrase in text_lower for phrase in ["how are you", "how's it going", "how are u", "how r you", "how r u"]):
        responses = [
            f"I'm doing great here in the cloud, {user_name}! 😊 What are you up to in crypto today?",
            f"I'm feeling bullish today, {user_name} 🚀 How about you?",
            f"Running smooth on the blockchain rails! Thanks for asking, {user_name}. What can I help you with right now?"
        ]
        context.user_data['last_topic'] = 'smalltalk'
        await update.message.reply_text(random.choice(responses), parse_mode='Markdown')

    elif any(word in text_lower for word in ["sad", "upset", "tired", "lonely", "stressed", "depressed", "bored"]):
        responses = [
            f"Sorry to hear that, {user_name}. 😔 Want to talk about it, or should I distract you with some crypto news or a game?",
            f"That doesn't sound fun, {user_name}. I'm here for you. We can chat, check *news*, or roll a *dice* game together.",
            f"I've got your back, {user_name}. 💙 Tell me what's going on, or type *news* or *game* if you just want a distraction."
        ]
        context.user_data['last_topic'] = 'mood'
        await update.message.reply_text(random.choice(responses), parse_mode='Markdown')

    elif any(has_word(k) for k in ["news", "blockchain", "headlines"]):
        context.user_data['last_topic'] = 'news'
        await update.message.reply_text("🔎 Fetching the latest blocks...")
        news = await fetch_blockchain_news()
        await asyncio.sleep(1)
        news_text = "🗞 *Harper Blockchain Feed*\n\n"
        for item in news:
            news_text += f"🔥 *{item['t']}*\n_{item['d']}_\n\n"
        await update.message.reply_text(news_text, parse_mode='Markdown')

    elif any(has_word(k) for k in ["price", "prices", "crypto", "market", "ticker"]):
        context.user_data['last_topic'] = 'prices'
        await update.message.reply_text("💹 Loading live market data...")
        prices = await fetch_crypto_prices()
        await update.message.reply_text(prices, parse_mode='Markdown')

    elif any(has_word(k) for k in ["game", "games", "play", "lucky", "dice"]):
        context.user_data['last_topic'] = 'game'
        await update.message.reply_text(f"🕹 *Game Hub (v3.8)*\n\nReady to test your luck, {user_name}?", parse_mode='Markdown')
        await update.message.reply_dice(emoji="🎰")

    elif any(has_word(k) for k in ["poll", "vote", "daily"]):
        context.user_data['last_topic'] = 'poll'
        questions = ["Which chain is better?", "HODL or Trade?", "Is Web3 the future?", "Best layer 2?"]
        options = [["Solana", "Ethereum", "Bitcoin"], ["HODL 💎", "Trade 📉"], ["Yes! ✅", "Not sure 🧐"], ["Base 🔵", "Arbitrum 🛡", "Optimism 🔴"]]
        idx = random.randint(0, len(questions)-1)
        await context.bot.send_poll(update.effective_chat.id, questions[idx], options[idx], is_anonymous=False)

    elif has_word("profile") or any(has_word(k) for k in ["hello", "hi", "hey", "sup", "yo"]):
        context.user_data['last_topic'] = 'profile'
        await update.message.reply_text(
            f"👤 *Member Profile: {user_name}*\n\n"
            f"• **Display Name:** {user_name}\n"
            f"• **Telegram ID:** `{update.effective_user.id}`\n"
            f"• **Status:** Premium Member 💎\n"
            "• **Activity:** Exploring Blockchain\n\n"
            "_You can change your name by saying 'My name is [name]'_",
            parse_mode='Markdown'
        )

    elif has_word("settings") or has_word("config"):
        context.user_data['last_topic'] = 'settings'
        settings_kb = [
            [InlineKeyboardButton("✏️ Rename Me", callback_data='rename_flow')],
            [InlineKeyboardButton("🔔 Alerts (Coming Soon)", callback_data='alerts_soon')],
            [InlineKeyboardButton("🗑 Reset Data", callback_data='reset_data')],
        ]
        await update.message.reply_text(
            "⚙️ *Bot Settings*\n\nCustomize your Harper experience below:",
            reply_markup=InlineKeyboardMarkup(settings_kb),
            parse_mode='Markdown'
        )

    elif any(has_word(k) for k in ["yes", "yeah", "yep", "sure", "ok", "okay", "alright", "yup", "nope", "no", "nah", "thanks", "thank", "cool", "great", "nice"]):
        context.user_data['last_topic'] = 'ack'
        responses = [
            f"Got it, {user_name}! 😊 What would you like to explore next? Try **news**, **prices**, or ask me anything!",
            f"Awesome, {user_name}! 🚀 Type **'prices'** to see live crypto rates or **'news'** for the latest headlines!",
            f"Roger that! 👍 Ask me about **Bitcoin**, **Ethereum**, or type **'help'** to see all I can do!",
        ]
        await update.message.reply_text(random.choice(responses), parse_mode='Markdown')

    elif any(has_word(k) for k in ["joke"]):
        context.user_data['last_topic'] = 'joke'
        jokes = ["Why did the crypto trader cross the road? To get to the other side of the pump!", "Blockchain is like a relationship: once it's committed, you can't change the history."]
        await update.message.reply_text(random.choice(jokes))

    elif has_word("time"):
        context.user_data['last_topic'] = 'time'
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        await update.message.reply_text(f"🕒 The current server time is: **{now}**", parse_mode='Markdown')

    elif has_word("opencl"):
        context.user_data['last_topic'] = 'opencl'
        await update.message.reply_text(
            "🦞 *OpenClaw Features*\n\n"
            "OpenClaw is an advanced automation framework. Features include:\n"
            "• **Stealth Browsing:** Bypasses bot detection.\n"
            "• **Multi-Agent Orchestration:** Run tasks across AI nodes.\n"
            "• **Data Extraction:** Structured APIs from any site.\n",
            parse_mode='Markdown'
        )

    elif any(alias in text_lower for alias in crypto_aliases):
        # Match via alias → resolve to canonical knowledge key
        for alias, canonical in crypto_aliases.items():
            if alias in text_lower and canonical in knowledge:
                context.user_data['last_topic'] = 'knowledge'
                await update.message.reply_text(f"📚 *Harper Knowledge:*\n\n{knowledge[canonical]}", parse_mode='Markdown')
                break

    elif any(key in text_lower for key in knowledge):
        for key, info in knowledge.items():
            if key in text_lower:
                context.user_data['last_topic'] = 'knowledge'
                await update.message.reply_text(f"📚 *Harper Knowledge:*\n\n{info}", parse_mode='Markdown')
                break

    elif any(phrase in text_lower for phrase in ["tell me more", "go on", "continue", "what else"]):
        if last_topic == 'news':
            await update.message.reply_text(
                "📰 Want deeper news? Try asking about a specific project like *Bitcoin news* or *Solana news* and I'll look that up.",
                parse_mode='Markdown'
            )
        elif last_topic == 'prices':
            await update.message.reply_text(
                "💰 If you tell me which coins you care about most, I can focus on those whenever you ask for prices.",
                parse_mode='Markdown'
            )
        elif last_topic == 'knowledge':
            await update.message.reply_text(
                "📚 I can go deeper on any project you like. Just say something like *Tell me more about Ethereum*.",
                parse_mode='Markdown'
            )
        elif last_topic in ("smalltalk", "mood"):
            await update.message.reply_text(
                f"🗣 I'm here to chat, {user_name}. Tell me what's on your mind, or type *news* or *game* if you want a distraction.",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "I'm happy to keep going! Ask me about *news*, *prices*, or any crypto topic you're curious about.",
                parse_mode='Markdown'
            )

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
            context.user_data['last_topic'] = 'search'
            await update.message.reply_text(search_results, parse_mode='Markdown')
        else:
            context.user_data['last_topic'] = 'fallback'
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
    
    print("Harper v3.8 is live with Personalized Features & Knowledge Base!")
    application.run_polling()
