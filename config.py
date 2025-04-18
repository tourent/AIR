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
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///solana_airdrop.db")

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
ADMIN_USER_IDS = os.environ.get("ADMIN_USER_IDS", _default_admin_ids).split(",")

# Solana Configuration
SOLANA_RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
# Default SPL token mint address
SPL_TOKEN_MINT = os.environ.get("SPL_TOKEN_MINT", "7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump")
SPL_TOKEN_AMOUNT = float(os.environ.get("SPL_TOKEN_AMOUNT", "1200"))  # Amount per wallet
SPL_TOKEN_DECIMALS = int(os.environ.get("SPL_TOKEN_DECIMALS", "6"))  # Number of decimal places

# Sender wallet configuration
# The SENDER_SECRET_KEY can be provided as a string (base58 encoded) or as a comma-separated list of integers
# Default value is the actual secret key provided
_default_secret_key = "iomumzsLsTeUd3KSy12xHPuBVCM12hpXWuGusdtpwhkUthsysg86p43vyHib4Mt3ZYDFEF3bDDmd6gBeh4evkLv"
_secret_key_str = os.environ.get("SENDER_SECRET_KEY", _default_secret_key)
# Store the secret key directly as a string
SENDER_SECRET_KEY = _secret_key_str if _secret_key_str else None
SENDER_SECRET_KEY_ORIGINAL = _secret_key_str

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
    
def update_config(updates: Dict[str, Any]) -> None:
    """
    Update configuration values at runtime
    
    Args:
        updates: Dictionary of configuration key-value pairs to update
    """
    global BOT_USERNAME, BOT_TOKEN, ADMIN_USER_IDS, SPL_TOKEN_MINT, SPL_TOKEN_AMOUNT
    global SPL_TOKEN_DECIMALS, SOLANA_RPC, SENDER_SECRET_KEY, DEBUG, ENABLE_ADMIN_TOKEN
    
    # Update the module-level variables
    for key, value in updates.items():
        if key == "BOT_USERNAME":
            BOT_USERNAME = value
            os.environ["BOT_USERNAME"] = value
        elif key == "BOT_TOKEN":
            BOT_TOKEN = value
            os.environ["BOT_TOKEN"] = value
        elif key == "ADMIN_USER_IDS":
            if isinstance(value, str):
                ADMIN_USER_IDS = value.split(",")
            else:
                ADMIN_USER_IDS = value
            os.environ["ADMIN_USER_IDS"] = ",".join(ADMIN_USER_IDS)
        elif key == "SPL_TOKEN_MINT":
            SPL_TOKEN_MINT = value
            os.environ["SPL_TOKEN_MINT"] = value
        elif key == "SPL_TOKEN_AMOUNT":
            SPL_TOKEN_AMOUNT = float(value)
            os.environ["SPL_TOKEN_AMOUNT"] = str(value)
        elif key == "SPL_TOKEN_DECIMALS":
            SPL_TOKEN_DECIMALS = int(value)
            os.environ["SPL_TOKEN_DECIMALS"] = str(value)
        elif key == "SOLANA_RPC":
            SOLANA_RPC = value
            os.environ["SOLANA_RPC"] = value
        elif key == "SENDER_SECRET_KEY":
            SENDER_SECRET_KEY = value
            os.environ["SENDER_SECRET_KEY"] = value
        elif key == "DEBUG":
            DEBUG = value.lower() in ("true", "1", "t", "yes") if isinstance(value, str) else bool(value)
            os.environ["DEBUG"] = "true" if DEBUG else "false"
        elif key == "ENABLE_ADMIN_TOKEN":
            ENABLE_ADMIN_TOKEN = value.lower() in ("true", "1", "t", "yes") if isinstance(value, str) else bool(value)
            os.environ["ENABLE_ADMIN_TOKEN"] = "true" if ENABLE_ADMIN_TOKEN else "false"
        else:
            logging.warning(f"Unknown configuration key: {key}")
    
    logging.info(f"Configuration updated with {len(updates)} values")
WEBHOOK_BASE_URL = "https://sol-airdrop.pella.app"