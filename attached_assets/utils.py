"""
Utility functions for the Solana Airdrop Application.
Provides functionality for both web interface and Telegram bot.
This is a simplified version without direct Solana dependencies for development.
"""
import logging
import os
import re
import base58
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize Solana client placeholder
SOLANA_RPC = os.environ.get("SOLANA_RPC", "https://api.mainnet-beta.solana.com")

def validate_solana_address(address: str) -> bool:
    """
    Validate if a string is a valid Solana address.
    
    Args:
        address: The address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Simple validation for development:
        # Solana addresses are base58-encoded and 32-44 characters long
        if not re.match(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', address):
            return False
            
        # Try to decode as base58 (should be 32 bytes)
        decoded = base58.b58decode(address)
        return len(decoded) == 32
    except Exception as e:
        logger.debug(f"Invalid Solana address: {e}")
        return False

def format_solana_address(address: str) -> str:
    """
    Format a Solana address for display (truncate middle).
    
    Args:
        address: The address to format
        
    Returns:
        str: Formatted address (e.g., "AiLH3...j41M")
    """
    if len(address) <= 12:
        return address
    
    return f"{address[:5]}...{address[-4:]}"

def sol_to_lamports(sol_amount: float) -> int:
    """
    Convert SOL to lamports.
    
    Args:
        sol_amount: Amount in SOL
        
    Returns:
        int: Amount in lamports
    """
    return int(sol_amount * 1_000_000_000)

def lamports_to_sol(lamports: int) -> float:
    """
    Convert lamports to SOL.
    
    Args:
        lamports: Amount in lamports
        
    Returns:
        float: Amount in SOL
    """
    return lamports / 1_000_000_000

def format_token_amount(amount: int, decimals: int) -> str:
    """
    Format a token amount with the correct number of decimals.
    
    Args:
        amount: Raw token amount
        decimals: Number of decimal places
        
    Returns:
        str: Formatted token amount
    """
    if decimals == 0:
        return str(amount)
    
    amount_str = str(amount).zfill(decimals + 1)
    
    integer_part = amount_str[:-decimals] or "0"
    fractional_part = amount_str[-decimals:]
    
    # Remove trailing zeros in fractional part
    fractional_part = fractional_part.rstrip("0")
    
    if fractional_part:
        return f"{integer_part}.{fractional_part}"
    else:
        return integer_part

def derive_token_address(wallet_address: str, token_mint: str) -> str:
    """
    Derive the associated token account address for a wallet and mint.
    This is a simplified mock version for development.
    
    Args:
        wallet_address: Wallet address
        token_mint: Token mint address
        
    Returns:
        str: Associated token account address
    """
    # In real implementation, this would call SPL Token program to derive ATA
    return f"ATA-{wallet_address[:5]}-{token_mint[:5]}"

async def process_airdrop_transaction(
    wallet_address: str,
    token_mint: str,
    token_amount: float,
    token_decimals: int,
    sender_secret_key=None
) -> dict:
    """
    Process a single airdrop transaction.
    This is a mock implementation for development.
    
    Args:
        wallet_address: Recipient wallet address
        token_mint: SPL token mint address
        token_amount: Amount of tokens to send
        token_decimals: Number of decimal places for the token
        sender_secret_key: Secret key for the sender wallet (can be a base58 string or a list of integers)
        
    Returns:
        dict: Result of the transaction with signature or error
    """
    try:
        # Log the transaction details
        logger.info(f"Mock airdrop: Sending {token_amount} tokens to {wallet_address}")
        
        # Simple validation
        if not validate_solana_address(wallet_address):
            return {
                "success": False,
                "error": f"Invalid wallet address: {wallet_address}"
            }
            
        if not validate_solana_address(token_mint):
            return {
                "success": False,
                "error": f"Invalid token mint: {token_mint}"
            }
        
        # Check if we have a valid secret key (either as base58 string or list of integers)
        if not sender_secret_key:
            return {
                "success": False,
                "error": "No sender secret key provided"
            }
        
        # Log the type of secret key for debugging (without revealing the key itself)
        logger.debug(f"Secret key type: {type(sender_secret_key).__name__}")
        
        # In a real implementation, we would convert the secret key to the right format
        # and use it to sign the transaction
        
        # For mock implementation, generate a fake signature
        import hashlib
        fake_signature = hashlib.sha256(
            f"{wallet_address}-{token_mint}-{token_amount}-{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        # Return a success response
        return {
            "success": True,
            "signature": fake_signature,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in airdrop transaction: {e}")
        return {
            "success": False,
            "error": str(e)
        }
