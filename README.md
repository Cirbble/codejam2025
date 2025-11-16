# Memecoin Sentiment Scraper & Automated Trading Bot

A comprehensive system for scraping Reddit posts about memecoins, analyzing sentiment and token mentions, and executing automated trades on Solana using Jupiter Aggregator.

## 🎯 Project Overview

This project was built for a hackathon to demonstrate automated sentiment analysis and trading of memecoins. It combines:

- **Web Scraping**: Automated Reddit scraping using Browser Cash's hosted browsers
- **AI Analysis**: Token identification using Browser Cash's Agent API
- **Automated Trading**: Buy/sell execution on Solana via Jupiter Aggregator

## 🏗️ Architecture

### Components

1. **Browser Cash Integration** (`src/browser_cash_client.py`)
   - Manages remote browser sessions via Browser Cash API
   - Uses Playwright with CDP (Chrome DevTools Protocol) for browser control
   - Handles navigation, script execution, and session management

2. **Reddit Scraper** (`src/reddit_scraper.py`)
   - Scrapes posts from multiple subreddits simultaneously
   - Extracts post metadata (title, content, upvotes, comments, timestamps)
   - Navigates to individual posts to scrape comments
   - Filters posts from the past week
   - Handles infinite scroll to load more posts

3. **Agent API Client** (`src/agent_client.py`)
   - Uses Browser Cash Agent API for AI-powered token identification
   - Analyzes post titles, content, and comments to identify token names
   - Implements queuing with semaphore to prevent session limit errors
   - Includes retry logic with exponential backoff

4. **Jupiter Trading Client** (`src/jupiter_client.py`)
   - Interfaces with Jupiter Aggregator API for Solana token swaps
   - Token address lookup (with Birdeye fallback)
   - Price quotes and swap execution
   - Transaction signing using Solana Web3.py

5. **Data Models** (`src/models.py`)
   - `Post` dataclass for structured scraped data
   - JSON serialization support

## 📋 Features

### Scraping Features
- ✅ **Parallel Subreddit Scraping**: Scrapes 3 subreddits simultaneously (`altcoin`, `CryptoMoonShots`, `pumpfun`)
- ✅ **Historical Scraping**: Scrapes all posts from the past week
- ✅ **Comment Extraction**: Navigates to each post to scrape comments
- ✅ **Infinite Scroll**: Aggressively scrolls to load more posts
- ✅ **Duplicate Prevention**: Tracks seen posts to avoid duplicates
- ✅ **Incremental Saving**: Saves posts to JSON in real-time as they're scraped
- ✅ **Thread-Safe**: Uses locks to prevent JSON file corruption with parallel instances

### Token Identification
- ✅ **Regex Fallback**: Fast `$TOKEN` pattern matching in titles (2-5 characters)
- ✅ **AI Analysis**: Uses Agent API to analyze post content + comments for token names
- ✅ **Queued Processing**: Agent calls are queued globally to prevent session limits
- ✅ **Retry Logic**: Automatic retries with exponential backoff on failures

### Trading Features
- ✅ **Token Lookup**: Finds token addresses from ticker symbols
- ✅ **Price Quotes**: Gets swap quotes from Jupiter
- ✅ **Automated Swaps**: Executes buy/sell orders on Solana
- ✅ **Transaction Signing**: Signs transactions with private key from `.env`
- ✅ **Error Handling**: Robust error handling and retry logic

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Browser Cash API key (Browser API + Agent API)
- Solana wallet with private key (for trading)
- `.env` file with API keys and wallet credentials

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Cirbble/codejam2025.git
cd codejam2025
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
python -m playwright install chromium
```

3. **Configure environment variables**:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
BROWSER_CASH_API_KEY=your_browser_api_key
AGENT_CASH_API_KEY=your_agent_api_key
MILAN_HOST=gcp-usc1-1.milan-taurine.tera.space
SOLANA_PRIVATE_KEY=your_solana_private_key_here
```

### Getting Your Solana Private Key

If you have a Phantom wallet with a 12-word recovery phrase:

1. Use a tool like `mnemonic` library to convert seed phrase to private key
2. The private key should be 64 bytes (128 hex characters)
3. Store it securely in `.env` (never commit to git!)

**⚠️ Security Warning**: Never share your private key or commit it to version control!

## 📖 Usage

### Running the Scraper

```bash
python main.py
```

This will:
1. Start 3 parallel browser sessions (one per subreddit)
2. Scrape posts from the past week
3. Extract comments from each post
4. Identify tokens using AI (queued to prevent session limits)
5. Save all data to `scraped_posts.json` incrementally

### Output Format

Posts are saved to `scraped_posts.json` with the following structure:

```json
{
  "id": 1,
  "source": "r/pumpfun",
  "platform": "reddit",
  "title": "Check out $TOKEN - going to the moon!",
  "content": "Post content here...",
  "author": "username",
  "timestamp": "2025-01-15T10:30:00Z",
  "post_age": "2 hours ago",
  "upvotes_likes": 42,
  "comment_count": 5,
  "comments": ["Comment 1", "Comment 2", ...],
  "link": "https://www.reddit.com/r/pumpfun/comments/...",
  "token_name": "TOKEN",
  "sentiment_score": null,
  "hype_score": null
}
```

### Testing Trading

Test buying a token:

```bash
python test_buy_hege.py
```

This will:
1. Check your wallet balance
2. Look up the token address
3. Get a quote for $1 worth
4. Execute the buy order
5. Display the transaction hash

## 🔧 Configuration

### Subreddits

Edit `src/config.py` to change which subreddits are scraped:

```python
MEMECOIN_SUBREDDITS = [
    "CryptoMoonShots",
    "SatoshiStreetBets",
    "altcoin",
    "pumpfun",
    # Add more...
]
```

### Parallel Scraping

Edit `main.py` to change which subreddits run in parallel:

```python
SUBREDDITS = ["altcoin", "CryptoMoonShots", "pumpfun"]
```

### Scraping Limits

In `main.py`, adjust `limit_per_subreddit` (posts per page):

```python
posts = scraper.scrape_all_subreddits(
    limit_per_subreddit=25,  # Posts per page
    scrape_comments=True,
    take_screenshots=False,
    output_file=output_file
)
```

## 🐛 Troubleshooting

### Session Limit Errors

If you see "Session limit reached" errors:

- The scraper uses a global semaphore to queue agent calls (max 1 concurrent)
- Browser sessions are limited by Browser Cash's API limits
- Try reducing the number of parallel instances

### Connection Errors

If you see `ERR_CONNECTION_RESET`:

- Reddit may be rate-limiting your requests
- The scraper includes retry logic with exponential backoff
- Try reducing the number of parallel instances

### Token Not Identified

If tokens aren't being identified:

- Check that Agent API has sufficient credits
- Verify the regex pattern matches (e.g., `$TOKEN` in title)
- Check agent logs for failures
- Ensure comments are being scraped (agent analyzes comments too)

### Trading Errors

If trading fails:

- Verify your wallet has sufficient SOL balance
- Check that the token address is correct
- Ensure Jupiter API is accessible (check DNS if needed)
- Verify your private key is correct (64 bytes)

## 📁 Project Structure

```
.
├── main.py                 # Main entry point (parallel scraping)
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in git)
├── scraped_posts.json     # Output file (generated)
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration (API keys, subreddits)
│   ├── models.py          # Data models (Post dataclass)
│   ├── browser_cash_client.py  # Browser Cash API client
│   ├── agent_client.py    # Agent API client (token identification)
│   ├── reddit_scraper.py  # Reddit scraping logic
│   ├── jupiter_client.py  # Jupiter trading client
│   └── twitter_scraper.py # Twitter scraper (not used)
├── test_buy_hege.py       # Test script for trading
├── test_jupiter.py        # Jupiter API test
├── test_network.py        # Network diagnostics
└── README.md              # This file
```

## 🔐 Security Notes

- **Never commit `.env` to git** - it contains sensitive API keys and private keys
- **Private keys**: Store securely, never share
- **API keys**: Rotate if exposed
- **Trading**: Start with small amounts for testing

## 🛠️ Technical Details

### Browser Cash Integration

- Uses Browser Cash's Session API to create remote browser sessions
- Connects via CDP (Chrome DevTools Protocol) using Playwright
- Handles navigation, script execution, and page interactions
- Manages session lifecycle (start, stop, cleanup)

### Agent API Integration

- Uses Browser Cash's Agent API for AI-powered analysis
- Sends post content + comments to agent for token identification
- Implements queuing to prevent session limit errors
- Includes retry logic for reliability

### Jupiter Integration

- Uses Jupiter Aggregator API (`lite-api.jup.ag`) for swaps
- Supports versioned transactions (v1 API)
- Handles token account creation (rent costs)
- Signs transactions with Solana Web3.py

### Threading & Concurrency

- Parallel subreddit scraping using `threading.Thread`
- Global semaphore for agent API calls (prevents session limits)
- Thread-safe JSON file updates using locks
- Global post ID counter for unique IDs across instances

## 📊 Performance

- **Scraping Speed**: ~3-5 posts per minute per subreddit (includes comment scraping)
- **Token Identification**: Queued, ~10-30 seconds per post (depending on queue)
- **Parallel Instances**: 3 subreddits scraped simultaneously
- **Memory Usage**: Moderate (browser sessions + Playwright)

## 🚧 Known Limitations

- Reddit rate limiting may slow down scraping
- Agent API session limits require queuing
- Browser Cash API has concurrent session limits
- Token identification accuracy depends on post content quality
- Trading requires sufficient SOL balance for gas + token account rent

## 📝 Future Improvements

- [ ] Sentiment analysis scoring
- [ ] Hype score calculation
- [ ] Automated trading based on sentiment thresholds
- [ ] Twitter/X integration
- [ ] Telegram channel monitoring
- [ ] Real-time monitoring (vs. historical scraping)
- [ ] Dashboard/UI for monitoring
- [ ] Database storage (vs. JSON files)
- [ ] More robust error recovery
- [ ] Performance optimizations

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

- **Browser Cash** for hosted browser infrastructure
- **Jupiter Aggregator** for Solana DEX aggregation
- **Reddit** for the platform we scrape
- **Solana** for the blockchain we trade on

---

**Built for CodeJam 2025** 🚀

