"""Configuration settings for Browser Cash API and project."""
import os
from dotenv import load_dotenv

load_dotenv()

# Browser Cash API Configuration
BROWSER_CASH_API_KEY = os.getenv("BROWSER_CASH_API_KEY")
AGENT_CASH_API_KEY = os.getenv("AGENT_CASH_API_KEY")
# Try both possible base URLs - we'll test which one works
BROWSER_CASH_BASE_URL = "https://browser-api.browser.cash/v1/consumer"
# Alternative: "https://browser-api.browser.cash/v1"
AGENT_CASH_BASE_URL = "https://agent-api.browser.cash"  # Base URL without /v1

# Milan host for CDP connections (e.g., "gcp-usc1-1.milan-taurine.tera.space")
# Check Browser Cash dashboard or try common patterns if not set
MILAN_HOST = os.getenv("MILAN_HOST", "gcp-usc1-1.milan-taurine.tera.space")

# Reddit Subreddits to monitor for memecoins
MEMECOIN_SUBREDDITS = [
    "CryptoMoonShots",
    "SatoshiStreetBets",
    "CryptoCurrencyTrading",
    "altcoin",
    "defi",
    "ethereum",
    "solana",
    "dogecoin",
    "shibainu",
]

# Memecoin-specific keywords to track
MEMECOIN_KEYWORDS = [
    "memecoin",
    "meme coin",
    "pump",
    "moon",
    "gem",
    "diamond hands",
    "to the moon",
    "hodl",
    "ape",
    "wen moon",
]

# Additional sites to scrape (Twitter/X, Telegram, etc.)
TWITTER_HANDLES = [
    "cryptocurrency",
    "CryptoMoonShots",
    # Add more Twitter handles
]

TELEGRAM_CHANNELS = [
    # Add Telegram channel IDs
]

