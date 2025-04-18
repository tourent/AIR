"""
Telegram bot implementation for Solana Airdrop Bot.
This module handles all Telegram bot interactions for wallet registration
and airdrop notifications.
"""
import logging
import asyncio
import threading
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

import config
import presets
from models import User, WalletAddress, AirdropEvent, AirdropTransaction
from app import db
from utils import validate_solana_address, format_solana_address, process_airdrop_transaction

logger = logging.getLogger(__name__)

# Global reference to the bot instance
telegram_bot = None

def is_running() -> bool:
    """Check if the Telegram bot is running"""
    return telegram_bot is not None and telegram_bot.is_running

class TelegramBot:
    """Telegram bot for Solana airdrop management"""
    
    def __init__(self, token: str):
        """Initialize the bot with a token"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.is_running = False
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("register", self.register_command))
        self.application.add_handler(CommandHandler("wallet", self.wallet_command))
        self.application.add_handler(CommandHandler("airdrop", self.airdrop_command))
        
        # Message handlers (for non-command messages)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        await update.message.reply_text(presets.WELCOME_MESSAGE)
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        await update.message.reply_text(presets.HELP_MESSAGE)
        
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /register command to register wallet addresses"""
        if not context.args:
            await update.message.reply_text(presets.REGISTER_USAGE)
            return
            
        wallet_address = context.args[0]
        
        # Validate address
        if not validate_solana_address(wallet_address):
            await update.message.reply_text(presets.REGISTER_INVALID)
            return
            
        # Get or create user
        user = self._get_or_create_user(update.effective_user)
        
        # Check if wallet already exists for this user
        existing_wallet = WalletAddress.query.filter_by(
            address=wallet_address,
            user_id=user.id
        ).first()
        
        if existing_wallet:
            await update.message.reply_text(presets.REGISTER_ALREADY_EXISTS)
            return
            
        # Create new wallet address
        wallet = WalletAddress(
            address=wallet_address,
            user_id=user.id,
            label=f"Telegram {datetime.utcnow().strftime('%Y-%m-%d')}"
        )
        
        db.session.add(wallet)
        db.session.commit()
        
        # Send confirmation
        formatted_address = format_solana_address(wallet_address)
        await update.message.reply_text(
            presets.REGISTER_SUCCESS.format(formatted_address)
        )
        
    async def wallet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /wallet command to show registered wallets"""
        # Get user
        user = self._get_or_create_user(update.effective_user)
        
        # Get all wallets for this user
        try:
            wallets = WalletAddress.query.filter_by(user_id=user.id).all()
            
            if not wallets:
                await update.message.reply_text(presets.WALLET_NONE)
                return
                
            if len(wallets) == 1:
                wallet_text = format_solana_address(wallets[0].address)
                await update.message.reply_text(
                    presets.WALLET_DISPLAY.format(wallet_text)
                )
            else:
                wallet_list = "\n".join([
                    f"{i+1}. {format_solana_address(w.address)}"
                    for i, w in enumerate(wallets)
                ])
                await update.message.reply_text(
                    presets.WALLET_MULTIPLE.format(wallet_list)
                )
                
        except Exception as e:
            logger.error(f"Error retrieving wallets: {e}")
            await update.message.reply_text(presets.WALLET_ERROR)
            
    async def airdrop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /airdrop command (admin only)"""
        # Check if user is admin
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text(presets.ADMIN_ONLY)
            return
            
        # Check arguments
        if len(context.args) < 1:
            await update.message.reply_text(presets.AIRDROP_USAGE)
            return
            
        # Parse arguments
        token_mint = context.args[0] if len(context.args) > 0 else config.SPL_TOKEN_MINT
        
        try:
            amount = float(context.args[1]) if len(context.args) > 1 else config.SPL_TOKEN_AMOUNT
            decimals = int(context.args[2]) if len(context.args) > 2 else config.SPL_TOKEN_DECIMALS
        except ValueError:
            await update.message.reply_text(presets.AIRDROP_INVALID_ARGS)
            return
            
        # Check if sender wallet is configured
        if not config.SENDER_SECRET_KEY:
            await update.message.reply_text(presets.AIRDROP_NO_SENDER)
            return
            
        # Get all registered wallets
        wallets = WalletAddress.query.all()
        
        if not wallets:
            await update.message.reply_text(presets.AIRDROP_NO_WALLETS)
            return
            
        # Create airdrop event
        user = self._get_or_create_user(update.effective_user)
        airdrop = AirdropEvent(
            token_mint=token_mint,
            token_amount=amount,
            token_decimals=decimals,
            started_by=user.id
        )
        db.session.add(airdrop)
        db.session.commit()
        
        # Send response that airdrop has started
        await update.message.reply_text(
            presets.AIRDROP_STARTED.format(amount, len(wallets))
        )
        
        # Start airdrop in background
        asyncio.create_task(self._process_airdrop(airdrop.id, wallets, token_mint, amount, decimals))
        
    async def _process_airdrop(self, event_id: int, wallets: List[WalletAddress], 
                              token_mint: str, amount: float, decimals: int):
        """Process airdrop transactions in background"""
        logger.info(f"Starting airdrop {event_id} to {len(wallets)} wallets")
        
        for wallet in wallets:
            # Create transaction record
            transaction = AirdropTransaction(
                event_id=event_id,
                wallet_address=wallet.address,
                status='pending'
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Process transaction
            try:
                result = await process_airdrop_transaction(
                    wallet_address=wallet.address,
                    token_mint=token_mint,
                    token_amount=amount,
                    token_decimals=decimals,
                    sender_secret_key=config.SENDER_SECRET_KEY
                )
                
                # Update transaction record
                transaction.status = 'success' if result['success'] else 'failed'
                transaction.transaction_signature = result.get('signature', None)
                transaction.error_message = result.get('error', None)
                transaction.completed_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                logger.error(f"Error processing airdrop to {wallet.address}: {e}")
                transaction.status = 'failed'
                transaction.error_message = str(e)
                transaction.completed_at = datetime.utcnow()
                db.session.commit()
        
        logger.info(f"Airdrop {event_id} completed")
       
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        message_text = update.message.text.strip()
        
        # Check if this is a wallet address (for easy registration)
        if validate_solana_address(message_text):
            # Create command context with the address as an argument
            context.args = [message_text]
            await self.register_command(update, context)
            return
        
        # Check for common keywords and give appropriate responses
        lowercase_text = message_text.lower()
        
        # Direct matches from common responses
        if lowercase_text in presets.COMMON_RESPONSES:
            await update.message.reply_text(presets.COMMON_RESPONSES[lowercase_text])
            return
            
        # Check for keywords
        for intent, keywords in presets.RECOGNIZED_KEYWORDS.items():
            if any(keyword in lowercase_text for keyword in keywords):
                if intent == "wallet":
                    await self.wallet_command(update, context)
                    return
                elif intent == "airdrop":
                    await update.message.reply_text(presets.COMMON_RESPONSES["airdrop"])
                    return
                elif intent == "help":
                    await self.help_command(update, context)
                    return
                elif intent == "greeting":
                    await update.message.reply_text(presets.COMMON_RESPONSES["hi"])
                    return
                elif intent == "thanks":
                    await update.message.reply_text(presets.COMMON_RESPONSES["thanks"])
                    return
                elif intent == "when":
                    await update.message.reply_text(presets.COMMON_RESPONSES["when"])
                    return
                elif intent == "info":
                    await update.message.reply_text(presets.COMMON_RESPONSES["token"])
                    return
        
        # Default response for unrecognized messages
        await update.message.reply_text(presets.UNRECOGNIZED_MESSAGE)
        
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Send message to user if possible
        if update and isinstance(update, Update) and update.effective_message:
            error_msg = presets.GENERIC_ERROR.format(str(context.error))
            await update.effective_message.reply_text(error_msg)
            
    def _get_or_create_user(self, telegram_user) -> User:
        """Get or create a user record for a Telegram user"""
        telegram_id = str(telegram_user.id)
        
        # Look for existing user
        user = User.query.filter_by(telegram_id=telegram_id).first()
        
        if not user:
            # Create new user
            username = telegram_user.username or f"tg_user_{telegram_id}"
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                username = f"{username}_{telegram_id}"
                
            user = User(
                username=username,
                email=f"{username}@telegram.example.com",  # Placeholder email
                telegram_id=telegram_id,
                is_admin=self._is_admin(telegram_id)
            )
            
            # Set a placeholder password (user can't login with this)
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(f"telegram_{telegram_id}")
            
            db.session.add(user)
            db.session.commit()
            
        return user
        
    def _is_admin(self, telegram_id) -> bool:
        """Check if a Telegram user ID is an admin"""
        return str(telegram_id) in config.ADMIN_USER_IDS
        
    def start(self):
        """Start the bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
            
        # Run the bot in a separate thread
        def run_bot():
            try:
                asyncio.set_event_loop(asyncio.new_event_loop())
                self.application.run_polling(allowed_updates=Update.ALL_TYPES)
            except Exception as e:
                logger.error(f"Error running Telegram bot: {e}")
                self.is_running = False
                
        self.bot_thread = threading.Thread(target=run_bot)
        self.bot_thread.daemon = True
        self.bot_thread.start()
        self.is_running = True
        logger.info("Telegram bot started")
        
    def stop(self):
        """Stop the bot"""
        if not self.is_running:
            logger.warning("Bot is not running")
            return
            
        try:
            # Stop the application
            if self.application:
                asyncio.run_coroutine_threadsafe(
                    self.application.stop(), 
                    self.application.update_queue.loop
                )
            self.is_running = False
            logger.info("Telegram bot stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
