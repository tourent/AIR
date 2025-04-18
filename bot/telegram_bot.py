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

# Flag to track bot running state
_running = False

def is_running() -> bool:
    """Check if the Telegram bot is running"""
    return _running

class TelegramBot:
    """Telegram bot implementation for the Solana Airdrop application"""
    
    def __init__(self, token=None):
        self.token = token
        self._running = False
        
    def is_running(self) -> bool:
        """Check if the bot is running"""
        return self._running
        
    def start(self) -> None:
        """Start the bot"""
        global _running
        if not self.token:
            logging.warning("No bot token provided. Bot not started.")
            return
        
        try:
            logging.info("Starting Telegram bot...")
            self._running = True
            _running = True
            logging.info("Telegram bot started")
            
        except Exception as e:
            logging.error(f"Error starting bot: {e}")
            self._running = False
            _running = False
            
    def stop(self) -> None:
        """Stop the bot"""
        global _running
        logging.info("Stopping bot...")
        self._running = False
        _running = False