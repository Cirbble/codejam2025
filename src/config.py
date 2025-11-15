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

# Reddit Subreddits for pump.fun and memecoin scraping (priority order)
# Top 3 are prioritized for parallel scraping
REDDIT_SUBREDDITS = [
    "pumpfun",              # Direct pump.fun subreddit (HIGHEST PRIORITY - Batch 1)
    "CryptoMoonShots",      # General memecoins (HIGH PRIORITY - Batch 1)
    "altcoin",              # Altcoin discussions (HIGH PRIORITY - Batch 1)
    "SolanaMemeCoins",      # Solana memecoins (Batch 2)
    "memecoin",             # General memecoin community (Batch 2)
    "SatoshiStreetBets",    # Crypto trading community (Batch 2)
    "solana",               # Solana blockchain (pump.fun is on Solana) (Batch 3)
]

# Twitter hashtags to monitor
TWITTER_HASHTAGS = [
    "SolanaMemeCoins",
    "memecoin",
    "pumpfunlaunch",
    "CryptoGains",
    "pumpfun",
]

