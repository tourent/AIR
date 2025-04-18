"""
Solana Airdrop Bot Web Application and Telegram Bot.
This application allows users to register Solana wallet addresses and 
admins to distribute SPL token airdrops via web interface or Telegram.
"""
import os
import threading
import logging
from datetime import datetime

from flask import Flask, g, request, jsonify

from app import app
import bot
import config
import routes

# Configure logging
logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

# Health check endpoint (must be defined before registering routes)
# to avoid conflict with other routes
@app.route("/api/health")
def health_check():
    """Simple health check endpoint"""
    telegram_status = "Running" if bot.is_running() else "Stopped"
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "telegram_bot": telegram_status
    })

# Add configuration context processor to all templates
@app.context_processor
def inject_config():
    """Add configuration to all templates"""
    return config.get_config_for_templates()

# Register routes with the application
routes.register_routes(app)

def start_telegram_bot():
    """Start the Telegram bot in a separate thread"""
    logger.info("Starting Telegram bot...")
    # Create telegram bot instance
    telegram_bot = bot.TelegramBot(token=config.BOT_TOKEN)
    bot.telegram_bot = telegram_bot
    # Start the bot
    telegram_bot.start()

def main():
    """
    Main entry point for the application.
    Starts the Flask web server and the Telegram bot (if configured).
    """
    # Start the Telegram bot if configured
    if config.BOT_TOKEN:
        telegram_thread = threading.Thread(target=start_telegram_bot)
        telegram_thread.daemon = True
        telegram_thread.start()
    else:
        logger.warning("Telegram bot not started: BOT_TOKEN not set")
    
    # The web server will be started by the calling code
    logger.info("Application initialized and ready")

if __name__ == "__main__":
    # Initialize the application
    main()
    
    # Start the Flask development server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=config.DEBUG)
