# Grammar Assistant Telegram Bot

An AI-powered Telegram bot that corrects grammar, spelling, punctuation, and improves sentence clarity.

## Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather

## Deploy on Railway

1. Push this code to GitHub
2. Connect your GitHub repo to Railway
3. Add `TELEGRAM_BOT_TOKEN` in Railway variables
4. Deploy!

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "TELEGRAM_BOT_TOKEN=your_token_here" > .env

# Run
python bot.py
