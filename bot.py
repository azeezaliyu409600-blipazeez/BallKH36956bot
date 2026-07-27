import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from flask import Flask, jsonify
import threading

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# Initialize Flask app for health checks
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return jsonify({"status": "healthy", "service": "grammar-bot"}), 200

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "grammar-bot"}), 200

# Initialize grammar correction service
class GrammarCorrector:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.use_openai = False
        self.use_groq = False
        
        if self.openai_key:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.use_openai = True
                logger.info("OpenAI initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        if not self.use_openai and self.groq_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_key)
                self.use_groq = True
                logger.info("Groq initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
        
        if not self.use_openai and not self.use_groq:
            logger.warning("No AI API keys found. Using basic correction.")
    
    async def correct_text(self, text: str) -> str:
        if not text or len(text.strip()) == 0:
            return "Please send me some text to correct!"
        
        if self.use_openai:
            return await self._correct_with_openai(text)
        elif self.use_groq:
            return await self._correct_with_groq(text)
        else:
            return self._basic_correction(text)
    
    async def _correct_with_openai(self, text: str) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """You are a grammar and writing expert. 
                    Correct the user's text for grammar, spelling, punctuation, and clarity 
                    while preserving the original meaning. Only return the corrected text, 
                    no explanations or additional comments."""},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI correction error: {e}")
            return f"Error: Could not correct text. Please try again later."
    
    async def _correct_with_groq(self, text: str) -> str:
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": """You are a grammar and writing expert. 
                    Correct the user's text for grammar, spelling, punctuation, and clarity 
                    while preserving the original meaning. Only return the corrected text, 
                    no explanations or additional comments."""},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq correction error: {e}")
            return f"Error: Could not correct text. Please try again later."
    
    def _basic_correction(self, text: str) -> str:
        import re
        corrected = text
        corrected = re.sub(r'\s+', ' ', corrected)
        corrected = re.sub(r'([.,!?])([A-Za-z])', r'\1 \2', corrected)
        sentences = re.split(r'([.!?])\s*', corrected)
        for i in range(0, len(sentences), 2):
            if sentences[i]:
                sentences[i] = sentences[i][0].upper() + sentences[i][1:] if sentences[i] else ''
        corrected = ''.join(sentences)
        return f"⚠️ Using basic correction mode.\n\n{corrected}"

# Initialize the grammar corrector
corrector = GrammarCorrector()

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = f"""👋 Hello {user.first_name}!

I'm your AI-powered grammar assistant bot. I can help you correct:
• Grammar mistakes
• Spelling errors
• Punctuation issues
• Sentence clarity

📝 Just send me any text and I'll correct it while preserving the original meaning!

🔧 Commands:
/help - Show help
/about - About this bot

Let's make your writing better! ✨"""
    
    keyboard = [
        [InlineKeyboardButton("📝 Try it now", switch_inline_query="")],
        [InlineKeyboardButton("❓ Need help?", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """📚 **How to use this bot:**

1️⃣ Send me any text message
2️⃣ I'll correct the grammar, spelling, and punctuation
3️⃣ I'll improve clarity while keeping your original meaning

**Commands:**
/start - Start the bot
/help - Show this help message
/about - Learn more about this bot

**Privacy:** Your messages are only processed for correction and not stored."""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = """🤖 **About Grammar Assistant Bot**

This bot uses advanced AI to help you improve your writing by:
• Correcting grammar and spelling errors
• Fixing punctuation mistakes
• Enhancing sentence clarity and flow
• Preserving your original meaning

**Technical Details:**
• Powered by advanced language models
• Instant corrections
• No storage of your messages

Made with ❤️ for better communication."""
    
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await update.message.chat.send_action(action="typing")
    
    try:
        corrected_text = await corrector.correct_text(user_text)
        response = f"📝 **Corrected Version:**\n\n{corrected_text}"
        
        original_length = len(user_text)
        corrected_length = len(corrected_text)
        if corrected_length > 0:
            response += f"\n\n📊 Original: {original_length} chars | Corrected: {corrected_length} chars"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error while processing your text. Please try again later."
        )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        help_text = """📚 **How to use this bot:**

1️⃣ Send me any text message
2️⃣ I'll correct the grammar, spelling, and punctuation
3️⃣ I'll improve clarity while keeping your original meaning

**Privacy:** Your messages are only processed for correction and not stored."""
        await query.edit_message_text(help_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")

def run_flask():
    """Run Flask app for health checks."""
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting Flask server on port {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def main():
    """Start the bot."""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server started in background thread")
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    
    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot is starting and polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
