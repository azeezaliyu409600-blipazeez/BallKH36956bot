# Grammar Assistant Telegram Bot

An AI-powered Telegram bot that corrects grammar, spelling, punctuation, and improves sentence clarity while preserving the original meaning.

## Deployment on Railway

### Quick Deploy Steps:

1. **Fork/Clone this repository to GitHub**

2. **Deploy on Railway:**
   - Go to [Railway.app](https://railway.app)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub and select the repository
   - Railway will automatically deploy

3. **Add Environment Variable:**
   - In your Railway dashboard, click on the deployed service
   - Go to "Variables" tab
   - Add: `TELEGRAM_BOT_TOKEN` = your_bot_token

4. **Wait for deployment to finish** (it will pass the health check)

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather

Optional (for better AI corrections):
- `OPENAI_API_KEY`: OpenAI API key
- `GROQ_API_KEY`: Groq API key

## Local Development

```bash
# Clone repository
git clone your-repo-url
cd telegram-grammar-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your token
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Run the bot
python bot.py
