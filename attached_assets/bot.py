"""
Telegram Bot for the Solana Airdrop Application.
Handles communication with users via Telegram.
"""
import logging
import asyncio
import threading
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import config
import presets
from utils import validate_solana_address, format_solana_address, process_airdrop_transaction

# Try to import telegram bot libraries but don't fail if they're not available
try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder, CommandHandler, MessageHandler, 
        ContextTypes, filters, CallbackContext
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logging.warning("python-telegram-bot not available. Bot will run in mock mode.")

# Try to import Solana specific libraries
try:
    from solana.publickey import PublicKey
    SOLANA_AVAILABLE = True
except ImportError:
    SOLANA_AVAILABLE = False
    logging.warning("Solana libraries not available. Using mock implementation.")

logger = logging.getLogger(__name__)

# Flag to track bot running state
_running = False

# In-memory storage for wallet addresses during development
wallets = {}  # user_id -> wallet_address

class TelegramBot:
    """Telegram bot implementation for the Solana Airdrop application"""
    
    def __init__(self, token=None):
        self.token = token or config.BOT_TOKEN
        self._running = False
        self.app = None
        
    def is_running(self) -> bool:
        """Check if the bot is running"""
        return self._running
        
    def start(self) -> None:
        """Start the bot"""
        if not self.token:
            logger.warning("No bot token provided. Bot not started.")
            return
        
        try:
            logger.info("Starting Telegram bot...")
            
            if TELEGRAM_AVAILABLE:
                # Start the bot in a separate thread
                threading.Thread(target=self._run_bot, daemon=True).start()
                self._running = True
                logger.info("Telegram bot started in background thread")
            else:
                # Mock mode for development
                logger.info("Running bot in mock mode (no actual Telegram connection)")
                self._running = True
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            self._running = False
            
    def _run_bot(self):
        """Run the actual telegram bot (called in a thread)"""
        try:
            # Create the Application
            self.app = ApplicationBuilder().token(self.token).build()
            
            # Command handlers
            self.app.add_handler(CommandHandler("start", self._handle_start))
            self.app.add_handler(CommandHandler("help", self._handle_help))
            self.app.add_handler(CommandHandler("register", self._handle_register_command))
            self.app.add_handler(CommandHandler("wallet", self._handle_wallet))
            self.app.add_handler(CommandHandler("airdrop", self._handle_airdrop))
            
            # Message handlers
            self.app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self._handle_message
            ))
            
            # Start the bot
            self.app.run_polling()
            
        except Exception as e:
            logger.error(f"Bot thread error: {e}")
            self._running = False
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command"""
        await update.message.reply_text(presets.WELCOME_MESSAGE)
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command"""
        await update.message.reply_text(presets.HELP_MESSAGE)
    
    async def _handle_register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /register command"""
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(presets.REGISTER_USAGE)
            return
        
        wallet_address = context.args[0].strip()
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        result = await self.register_wallet(user_id, wallet_address, username)
        await update.message.reply_text(result["message"])
    
    async def _handle_wallet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /wallet command"""
        user_id = str(update.effective_user.id)
        
        if user_id in wallets:
            wallet = wallets[user_id]
            await update.message.reply_text(presets.WALLET_DISPLAY.format(f"`{wallet}`"))
        else:
            await update.message.reply_text(presets.WALLET_NONE)
    
    async def _handle_airdrop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /airdrop command (admin only)"""
        user_id = str(update.effective_user.id)
        
        # Check if user is an admin
        if user_id not in config.ADMIN_USER_IDS:
            await update.message.reply_text(presets.ADMIN_ONLY)
            return
        
        # Extract arguments
        if not context.args or len(context.args) != 3:
            await update.message.reply_text(presets.AIRDROP_USAGE)
            return
        
        try:
            token_mint = context.args[0].strip()
            amount = float(context.args[1].strip())
            decimals = int(context.args[2].strip())
            
            result = await self.start_airdrop(user_id, token_mint, amount, decimals)
            await update.message.reply_text(result["message"])
            
        except ValueError:
            await update.message.reply_text(presets.AIRDROP_INVALID_ARGS)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages (primarily wallet addresses)"""
        text = update.message.text.strip().lower()
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        # Check if the message looks like a wallet address
        if validate_solana_address(text):
            result = await self.register_wallet(user_id, text, username)
            await update.message.reply_text(result["message"])
            return
            
        # Check for common responses
        if text in presets.COMMON_RESPONSES:
            await update.message.reply_text(presets.COMMON_RESPONSES[text])
            return
            
        # Check for keyword matches
        response_sent = False
        for category, keywords in presets.RECOGNIZED_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                if category == "wallet":
                    await self._handle_wallet(update, context)
                elif category == "airdrop":
                    await update.message.reply_text(presets.COMMON_RESPONSES["airdrop"])
                elif category == "help":
                    await self._handle_help(update, context)
                elif category == "greeting":
                    await update.message.reply_text(presets.COMMON_RESPONSES["hi"])
                elif category == "thanks":
                    await update.message.reply_text(presets.COMMON_RESPONSES["thanks"])
                elif category == "when":
                    await update.message.reply_text(presets.COMMON_RESPONSES["when"])
                elif category == "info":
                    await update.message.reply_text(presets.COMMON_RESPONSES["token"])
                response_sent = True
                break
                
        # If no keywords matched, send unrecognized message response
        if not response_sent:
            await update.message.reply_text(presets.UNRECOGNIZED_MESSAGE)
            
    def stop(self) -> None:
        """Stop the bot"""
        logger.info("Stopping bot...")
        if self.app:
            # In a real implementation, we would stop the app properly
            # For now, we just set the running flag to False
            pass
        self._running = False
        
    async def register_wallet(self, user_id: str, wallet_address: str, username: str = None) -> Dict[str, Any]:
        """
        Register a wallet address for a user
        
        Args:
            user_id: Telegram user ID
            wallet_address: Solana wallet address
            username: Telegram username (optional)
            
        Returns:
            Dict: Result of the registration
        """
        try:
            # Validate the wallet address
            if not validate_solana_address(wallet_address):
                return {
                    "success": False,
                    "message": presets.REGISTER_INVALID
                }
            
            # Check if wallet is already registered for this user
            if user_id in wallets and wallets[user_id] == wallet_address:
                return {
                    "success": False,
                    "message": presets.REGISTER_ALREADY_EXISTS
                }
            
            # Store the wallet (In a real implementation, this would save to the database)
            wallets[user_id] = wallet_address
            logger.info(f"User {user_id} ({username or 'unknown'}) registered wallet: {wallet_address}")
            
            # Save to database if we have a connection to the DB
            # In a real implementation, we would store in the database here
            
            formatted_wallet = f"`{wallet_address}`"
            return {
                "success": True,
                "message": presets.REGISTER_SUCCESS.format(formatted_wallet)
            }
            
        except Exception as e:
            logger.error(f"Error registering wallet: {e}")
            return {
                "success": False,
                "message": presets.GENERIC_ERROR.format(str(e))
            }
    
    async def start_airdrop(self, admin_id: str, token_mint: str, amount: float, decimals: int) -> Dict[str, Any]:
        """
        Start an airdrop to all registered wallets
        
        Args:
            admin_id: ID of the admin starting the airdrop
            token_mint: Solana SPL token mint address
            amount: Amount of tokens to send per wallet
            decimals: Number of decimal places for the token
            
        Returns:
            Dict: Result of starting the airdrop
        """
        # Check if user is admin
        if admin_id not in config.ADMIN_USER_IDS:
            return {
                "success": False,
                "message": "❌ Only admins can trigger airdrops."
            }
        
        # Check if there are wallets to airdrop to
        if not wallets:
            return {
                "success": False,
                "message": "❌ No wallets registered for airdrop."
            }
        
        # Check if sender secret key is set
        if not config.SENDER_SECRET_KEY:
            return {
                "success": False,
                "message": "❌ Sender wallet not configured. Please set the SENDER_SECRET_KEY environment variable."
            }
        
        # In a production implementation, this would process the airdrop
        # For now, we just log and simulate success
        logger.info(f"Admin {admin_id} started airdrop of {amount} tokens to {len(wallets)} wallets")
        
        # Start a background task to process the airdrop
        # In a real implementation, this would use a proper task queue
        asyncio.create_task(self._process_airdrop(token_mint, amount, decimals))
        
        return {
            "success": True,
            "message": f"✅ Started airdrop of {amount} tokens to {len(wallets)} wallets.\nProcessing in background...",
            "wallets": len(wallets)
        }
    
    async def _process_airdrop(self, token_mint: str, amount: float, decimals: int) -> None:
        """Process the airdrop in the background"""
        logger.info(f"Processing airdrop of {amount} tokens to {len(wallets)} wallets")
        
        for user_id, wallet_address in wallets.items():
            try:
                # Process the transaction (in a real implementation, this would use Solana SDK)
                # Use the original format string if available, otherwise fall back to the parsed version
                sender_key = config.SENDER_SECRET_KEY_ORIGINAL or config.SENDER_SECRET_KEY
                result = await process_airdrop_transaction(
                    wallet_address=wallet_address,
                    token_mint=token_mint,
                    token_amount=amount,
                    token_decimals=decimals,
                    sender_secret_key=sender_key
                )
                
                if result["success"]:
                    logger.info(f"Airdrop to {wallet_address} successful: {result['signature']}")
                else:
                    logger.error(f"Airdrop to {wallet_address} failed: {result['error']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing airdrop to {wallet_address}: {e}")
        
        logger.info("Airdrop processing completed")

# Create a single instance of the bot
telegram_bot = TelegramBot()

def is_running() -> bool:
    """Check if the Telegram bot is running"""
    return telegram_bot.is_running()