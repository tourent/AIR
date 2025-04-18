"""
Preset messages and responses for the Solana Airdrop Bot
"""

# Welcome messages
WELCOME_MESSAGE = """
🚀 Welcome to the $OVO Airdrop Bot! 🚀

This bot allows you to register your Solana wallet address to receive SPL token airdrops.

Commands:
/register <wallet_address> - Register your Solana wallet
/wallet - Check your registered wallet
/help - Show this help message

Alternatively, you can simply send your Solana wallet address.
"""

# Help messages
HELP_MESSAGE = """
🔍 Solana Airdrop Bot Commands:

/register <wallet_address> - Register your Solana wallet
/wallet - Check your registered wallet
/help - Show this help message

For admins only:
/airdrop - Trigger an airdrop to all registered wallets

You can also register by simply sending your Solana wallet address.
"""

# Registration messages
REGISTER_USAGE = """
Please provide your Solana wallet address.

Example: /register AiLH3qLGw9HVhQrQbZ82KGAY8tLnCyi8nG3LqAVMYwp4
"""

REGISTER_SUCCESS = """
✅ Wallet registered successfully!

{}

You will be notified when airdrops occur.
"""

REGISTER_INVALID = """
❌ Invalid Solana wallet address. Please check and try again.
"""

REGISTER_ALREADY_EXISTS = """
⚠️ This wallet is already registered for you.
"""

# Wallet information messages
WALLET_DISPLAY = """
Your registered wallet address:

{}
"""

WALLET_MULTIPLE = """
Your registered wallet addresses:

{}
"""

WALLET_NONE = """
You don't have a registered wallet address yet.

Use /register <wallet_address> to register your wallet.
"""

WALLET_ERROR = """
Unable to retrieve your wallet addresses. Please try again later.
"""

# Admin messages
ADMIN_ONLY = """
❌ This command is only available to admins.
"""

AIRDROP_USAGE = """
Admin command format:

/airdrop <token_mint_address> <amount> <decimals>

Example: /airdrop 7d7jZLzHHefeSDqJj9EJhTrA1Ujmsb3saxs5vPdtpump 10 0
"""

AIRDROP_INVALID_ARGS = """
Invalid arguments. Amount must be a number and decimals an integer.
"""

AIRDROP_NO_SENDER = """
❌ Sender wallet not configured. Please set the SENDER_SECRET_KEY environment variable.
"""

AIRDROP_NO_WALLETS = """
❌ No wallets registered for airdrop.
"""

AIRDROP_STARTED = """
✅ Started airdrop of {} tokens to {} wallets.
Processing in background...
"""

# Error messages
INVALID_WALLET_MESSAGE = """
That doesn't look like a valid Solana wallet address. Please check the address and try again.

Use /help to see available commands.
"""

GENERIC_ERROR = """
❌ An error occurred: {}
"""

# Common responses
COMMON_RESPONSES = {
    "hello": "👋 Hello! How can I help you today?",
    "hi": "👋 Hi there! Need help with Solana airdrops?",
    "thanks": "You're welcome! 😊",
    "thank you": "You're welcome! 😊",
    "airdrop": "To participate in airdrops, use /register <wallet_address> to register your Solana wallet.",
    "when": "Airdrops are scheduled by the admin. You'll be notified when one is available.",
    "how": "Just register your wallet with /register <wallet_address> and you'll be eligible for future airdrops!",
    "token": "We're distributing SPL tokens on the Solana blockchain. Register your wallet to participate!"
}

# Recognized keywords for bot responses
RECOGNIZED_KEYWORDS = {
    "wallet": ["wallet", "address", "key", "solana address"],
    "airdrop": ["airdrop", "drop", "free", "token", "giveaway"],
    "help": ["help", "assist", "support", "command", "how"],
    "greeting": ["hello", "hi", "hey", "greetings", "good day", "howdy"],
    "thanks": ["thanks", "thank you", "appreciate", "grateful"],
    "when": ["when", "date", "schedule", "time", "receive"],
    "info": ["what", "info", "about", "explain", "tell me"]
}

# Response for unrecognized messages
UNRECOGNIZED_MESSAGE = """
I didn't understand that message. Try using one of these commands:

/help - Show available commands
/register <wallet_address> - Register your wallet
/wallet - View your registered wallet
"""
