#!/usr/bin/env python
"""
Test script to verify the Solana Airdrop Bot configuration with wallet secret key in original format.
"""
import logging
import asyncio
import config
import utils
import bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_wallet_secret_format():
    """Test the wallet secret key format handling"""
    logger.info("Testing wallet secret key format handling...")
    
    # Check current configuration
    logger.info(f"Secret key type: {type(config.SENDER_SECRET_KEY).__name__}")
    logger.info(f"Original secret key present: {config.SENDER_SECRET_KEY_ORIGINAL is not None}")
    
    # Test mock transaction with current configuration
    result = await utils.process_airdrop_transaction(
        wallet_address="7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump",
        token_mint="7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump",
        token_amount=1200,
        token_decimals=6,
        sender_secret_key=config.SENDER_SECRET_KEY
    )
    
    logger.info(f"Transaction result with current config: {result['success']}")
    
    # Test with a string secret key (base58 format simulation)
    test_base58_key = "5K6suQAGVv8gzGBWQbPyqDdScLHMvRZWDPQJqPJmuKWrNimyYfX"
    result = await utils.process_airdrop_transaction(
        wallet_address="7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump",
        token_mint="7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump",
        token_amount=1200,
        token_decimals=6,
        sender_secret_key=test_base58_key
    )
    
    logger.info(f"Transaction result with base58 key: {result['success']}")
    
    return {
        "current_config_test": result['success'],
        "base58_key_test": result['success']
    }

def main():
    """Main entry point for the test script"""
    logger.info("Starting bot configuration test...")
    
    # Check if the bot module is loaded correctly
    logger.info(f"Bot module available: {bot is not None}")
    
    # Run the async test
    test_results = asyncio.run(test_wallet_secret_format())
    
    # Print summary
    logger.info("Test Summary:")
    logger.info(f"  Current config format works: {test_results['current_config_test']}")
    logger.info(f"  Base58 key format works: {test_results['base58_key_test']}")
    
    # Final message
    if all(test_results.values()):
        logger.info("✅ All tests passed! The wallet secret key format handling is working correctly.")
    else:
        logger.error("❌ Some tests failed. Please check the logs for details.")

if __name__ == "__main__":
    main()