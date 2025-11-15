# Memecoin Sentiment & Hype Tracker

Automated sentiment analysis and hype tracking for memecoins using Browser Cash API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python -m playwright install chromium
```

3. Create a `.env` file with your Browser Cash API keys:
```
BROWSER_CASH_API_KEY=your_browser_api_key_here
AGENT_CASH_API_KEY=your_agent_api_key_here
```

## Usage

Run the scraper:
```bash
python main.py
```

This will:
- Navigate to all configured Reddit subreddits
- Scrape posts with full details (title, content, upvotes, comments, etc.)
- Save results to `scraped_posts.json`

## Features

- Automated Reddit subreddit navigation via Browser Cash
- Full post details (title, content, author, timestamp, upvotes, comments)
- Comment scraping
- JSON output format
- Agent API fallback for complex tasks
- Screenshot support (optional)

