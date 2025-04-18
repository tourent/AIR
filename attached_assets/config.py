"""
Configuration settings for the Solana Airdrop Telegram Bot.
Environment variables are used to secure sensitive information.
"""
import os
import logging
from typing import List, Optional, Any, Dict
from datetime import datetime

# Basic Application Configuration
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "t", "yes")
SECRET_KEY = os.environ.get("SESSION_SECRET", "[203, 61, 17, 78, ..., 125]")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///instance/solana_airdrop.db")

# Admin Access Configuration
# This token allows admin access without authentication
ADMIN_ACCESS_TOKEN = os.environ.get("ADMIN_ACCESS_TOKEN", "TOKEN_123")
# Set to True to enable admin access via token
ENABLE_ADMIN_TOKEN = os.environ.get("ENABLE_ADMIN_TOKEN", "True").lower() in ("true", "1", "t", "yes")

# Telegram Bot Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7649112744:AAEmRzq86QIGGMQcsNXJldvv1f1sBl-ri8Y")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "@OVOCOINAIRDROP_bot")
# Default admin user IDs - users who can trigger airdrops
_default_admin_ids = "798521346"  # Add your Telegram user ID here
ADMIN_USER_IDS = os.environ.get("ADMIN_USER_IDS", "7134271831").split(",")

# Solana Configuration
SOLANA_RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
# Default SPL token mint address
SPL_TOKEN_MINT = os.environ.get("SPL_TOKEN_MINT", "7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump")
SPL_TOKEN_AMOUNT = float(os.environ.get("SPL_TOKEN_AMOUNT", "1200"))  # Amount per wallet
SPL_TOKEN_DECIMALS = int(os.environ.get("SPL_TOKEN_DECIMALS", "6"))  # Number of decimal places

# Sender wallet configuration
# The SENDER_SECRET_KEY should be provided as a comma-separated list of integers
# Default value is a placeholder for example purposes and should be replaced
_default_secret_key = "203,61,17,78,125"  # Shortened for security, replace with actual key
_secret_key_str = os.environ.get("SENDER_SECRET_KEY", _default_secret_key)
try:
    SENDER_SECRET_KEY = [int(i) for i in _secret_key_str.split(",")] if _secret_key_str else None
except Exception as e:
    logging.error(f"Failed to parse SENDER_SECRET_KEY: {e}")
    SENDER_SECRET_KEY = None

# Validate configuration
if not BOT_TOKEN:
    logging.warning("BOT_TOKEN not set. Please set this environment variable.")

if not ADMIN_USER_IDS or ADMIN_USER_IDS == [""]:
    logging.warning("No admin user IDs specified. Only admins can trigger airdrops.")

if not SENDER_SECRET_KEY:
    logging.warning("SENDER_SECRET_KEY not set. Airdrops will not function without a valid sender wallet.")

# Helper functions to pass data to templates
def get_config_for_templates() -> Dict[str, Any]:
    """Get a dictionary of configuration values for templates"""
    return {
        # Telegram Bot Configuration
        "BOT_USERNAME": BOT_USERNAME,
        "BOT_TOKEN": BOT_TOKEN is not None,  # Just pass if it's configured, not the actual token
        "ADMIN_USER_IDS": ADMIN_USER_IDS,
        
        # Solana Configuration
        "SPL_TOKEN_MINT": SPL_TOKEN_MINT,
        "SPL_TOKEN_AMOUNT": SPL_TOKEN_AMOUNT,
        "SPL_TOKEN_DECIMALS": SPL_TOKEN_DECIMALS,
        "SOLANA_RPC": SOLANA_RPC,
        
        # Sender Wallet Configuration
        "SENDER_SECRET_KEY": SENDER_SECRET_KEY is not None,  # Just pass if it's configured, not the actual key
        
        # Application Configuration
        "DEBUG": DEBUG,
        "ENABLE_ADMIN_TOKEN": ENABLE_ADMIN_TOKEN,
        "now": datetime.utcnow()
    }
