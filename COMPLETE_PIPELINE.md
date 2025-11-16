# 🎯 Complete Project Pipeline - Coin'ed (CodeJam 2025)

## 📋 Overview

**Coin'ed** is a comprehensive memecoin sentiment analysis and automated trading platform that scrapes Reddit, analyzes sentiment, fetches real blockchain data, displays results in a dashboard, and executes trades on Solana.

---

## 🔄 Complete Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: DATA COLLECTION                      │
│                        (Backend/Python)                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         main.py (3 Parallel Browser Sessions)
                              ↓
    ┌──────────────┬──────────────┬──────────────┐
    │              │              │              │
  r/altcoin   r/CryptoMoonShots  r/pumpfun
    │              │              │              │
    └──────────────┴──────────────┴──────────────┘
                              ↓
              scraped_posts.json (890 posts)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 2: SENTIMENT ANALYSIS                    │
│                        (Python/AI)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         sentiment_analysis/sentiment.py
                              ↓
              sentiment.json (with scores)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  STEP 3: BLOCKCHAIN DATA FETCH                  │
│                    (Python + APIs)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
      scrapper_and_analysis/convert_to_coin_data.py
                              ↓
         ┌─────────────────────────────────────┐
         │  Fetches from Multiple Sources:    │
         │  • DexScreener API (Solana)        │
         │  • Moralis API (Multi-chain)       │
         │  • PumpPortal API (pump.fun)       │
         │  • Jupiter Token List              │
         └─────────────────────────────────────┘
                              ↓
         coin-ed/public/coin-data.json
         (Real prices, addresses, logos)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 4: FRONTEND DISPLAY                     │
│                        (Angular)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              Angular Dashboard (coin-ed/)
                              ↓
         ┌─────────────────────────────────────┐
         │  Features:                          │
         │  • Live coin sidebar (sorted)       │
         │  • Top bar with AI toggles          │
         │  • Portfolio view                   │
         │  • Price charts (Chart.js)          │
         │  • Settings page                    │
         └─────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   STEP 5: AUTOMATED TRADING                     │
│                    (Solana/Jupiter)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
         src/jupiter_client.py
                              ↓
         Jupiter Aggregator API
                              ↓
         Executes Buy/Sell on Solana
```

---

## 🚀 STEP 1: Data Collection (main.py)

### How It Works

**File:** `main.py`  
**Output:** `scraped_posts.json`

### What You Need to Know

1. **Before running, DELETE current contents of scraped_posts.json**
   ```bash
   # Empty the file or delete it
   echo "[]" > scraped_posts.json
   ```

2. **Run the scraper:**
   ```bash
   python main.py
   ```

3. **What happens:**
   - Opens **3 browser tabs simultaneously** (via Browser Cash API)
   - Each tab scrapes a different subreddit:
     - Tab 1: `r/altcoin`
     - Tab 2: `r/CryptoMoonShots`
     - Tab 3: `r/pumpfun`
   - Scrapes posts from the **past week only**
   - Extracts for each post:
     - Title, content, author, timestamp
     - Upvotes, comment count
     - Comments (navigates to each post)
     - Token identification (regex or AI)

4. **Token Identification Methods:**
   - **Fast regex:** Looks for `$TOKEN` pattern (e.g., `$RAWW`, `$HEGE`)
   - **AI fallback:** Uses Browser Cash Agent API to analyze content
   - **Queued execution:** Global semaphore prevents session limits

5. **Output Format (scraped_posts.json):**
   ```json
   [
     {
       "id": 1,
       "source": "r/CryptoMoonShots",
       "platform": "reddit",
       "title": "The World's going full degen, be better",
       "content": "...",
       "author": "u/Ok_Poem_2813",
       "timestamp": "2025-11-15T18:55:00.254000+0000",
       "post_age": "9 hr. ago",
       "upvotes_likes": 10,
       "comment_count": 4,
       "comments": ["...", "..."],
       "link": "https://www.reddit.com/...",
       "token_name": "RAWW"
     }
   ]
   ```

### Key Features

- ✅ **Parallel execution** - 3 subreddits scraped simultaneously
- ✅ **Thread-safe** - Uses locks to prevent JSON corruption
- ✅ **Incremental saving** - Saves posts as they're scraped
- ✅ **Historical scraping** - Gets all posts from past week
- ✅ **Comment extraction** - Navigates to each post for comments
- ✅ **Duplicate prevention** - Tracks seen posts
- ✅ **AI-powered** - Token identification via Agent API

---

## 🧠 STEP 2: Sentiment Analysis (sentiment.py)

### How It Works

**File:** `sentiment_analysis/sentiment.py`  
**Input:** `scraped_posts.json`  
**Output:** `sentiment.json`

### Run It

```bash
cd sentiment_analysis
python sentiment.py
```

### What It Does

1. Reads `scraped_posts.json`
2. Analyzes each post for:
   - **Raw sentiment score** (-1 to 1)
   - **Aggregate sentiment score** (weighted)
   - **Engagement score** (based on upvotes/comments)
3. Outputs sentiment data to `sentiment.json`

### Output Format

```json
[
  {
    "token_name": "RAWW",
    "raw_sentiment_score": 0.8,
    "aggregate_sentiment_score": 0.85,
    "engagement_score": 0.6,
    "source": "r/CryptoMoonShots",
    ...
  }
]
```

---

## 🔗 STEP 3: Blockchain Data Enrichment (convert_to_coin_data.py)

### How It Works

**File:** `coin-ed/scrapper_and_analysis/convert_to_coin_data.py`  
**Input:** `sentiment.json`  
**Output:** `coin-ed/public/coin-data.json`

### Prerequisites

1. **Create .env file:**
   ```bash
   cd coin-ed/scrapper_and_analysis
   cp .env.example .env
   ```

2. **Add your Moralis API key to .env:**
   ```bash
   MORALIS_API_KEY=your_key_here
   ```

### Run It

```bash
cd coin-ed/scrapper_and_analysis
python convert_to_coin_data.py
```

### What It Does

1. **Reads sentiment.json** with token names
2. **For each token, fetches:**
   - **Token address** (Solana mint address)
   - **Real-time price** (USD)
   - **24h price change** (%)
   - **Token logo** (image URL)
   - **Liquidity data**
   - **DEX information**

3. **Data sources (priority order):**
   - **DexScreener API** (primary for Solana) - FREE
   - **Moralis Solana API** (fallback) - Requires key
   - **Moralis EVM** (Ethereum, BSC, Polygon)
   - **PumpPortal API** (pump.fun tokens)

4. **Combines with sentiment data:**
   - Sentiment scores
   - Engagement metrics
   - BUY/HOLD/SELL recommendation
   - Confidence score (0-100%)

### Output Format (coin-data.json)

```json
[
  {
    "id": "raww",
    "name": "RAWW",
    "symbol": "RAWW",
    "address": "8HqJySYJrkTqa1M4RWNBMSSnuoPRkscuLrCt3BrXjm5p",
    "price": 0.00000123,
    "balance": 813008.13,
    "decimals": 9,
    "logo": "https://cdn.dexscreener.com/...",
    "chain": "solana",
    "changePercentage": 0.0523,
    "raw_sentiment_score": 0.8,
    "aggregate_sentiment_score": 0.85,
    "engagement_score": 0.6,
    "confidence": 84,
    "recommendation": "BUY",
    "source": "r/CryptoMoonShots",
    "upvotes_likes": 10,
    "comment_count": 4,
    "comments": ["..."]
  }
]
```

### Success Rate

- **Typical: 85-90%** of tokens found with real data
- Example: 12 of 14 tokens found on Solana

---

## 🎨 STEP 4: Frontend Display (Angular Dashboard)

### How It Works

**Location:** `coin-ed/`  
**Input:** `public/coin-data.json`

### Run It

```bash
cd coin-ed
npm install
npm start
```

Open browser: **http://localhost:4200**

### Features

#### **Top Bar**
- **Left:** Logo (💰 Coin'ed)
- **Center:** AI Agent toggles
  - 🌐 Web Scraper
  - 💰 AI Buyer (locked until scraper ON)
  - 💸 AI Seller (locked until scraper ON)
- **Right:** Settings button (⚙️)

#### **Left Sidebar**
- **Live coin list** (auto-sorts by recency)
- **NEW badges** for recently scraped coins
- **Click to select** coin for details
- **Coin count** badge
- **Demo data button**

#### **Main Content**
- **Total balance** display
- **Coin cards** with mini charts
- **Portfolio** breakdown
- **Interactive charts** (Chart.js)
- **Price data** from blockchain

#### **Key UI Features**
- ✅ Dark theme with gold accents
- ✅ Responsive (mobile-friendly)
- ✅ Real-time updates
- ✅ Smooth animations
- ✅ Live sorting (newest first)

---

## 💰 STEP 5: Automated Trading (Jupiter API)

### How It Works

**File:** `src/jupiter_client.py`  
**Platform:** Solana via Jupiter Aggregator

### Prerequisites

1. **Create .env file in project root:**
   ```bash
   cp .env.example .env
   ```

2. **Add your Solana private key:**
   ```bash
   SOLANA_PRIVATE_KEY=your_64_byte_private_key_here
   ```

### Features

- ✅ **Token lookup** by symbol or address
- ✅ **Price quotes** from Jupiter
- ✅ **Buy/sell execution** on Solana
- ✅ **Transaction signing** with private key
- ✅ **Aggregates liquidity** from all Solana DEXs

### Test It

```bash
python test_buy_hege.py
```

### Current Status

⚠️ **DNS issues** with Jupiter API endpoints  
See: `FIX_DNS.md`, `SOLUTIONS.md`, `WORKAROUND.md`

**Workaround:**
- Change DNS to Google DNS (8.8.8.8)
- Or wait for Jupiter API recovery
- Or use manual trading on jup.ag

---

## 🔐 Security & API Keys

### API Keys Needed

| API | Purpose | Required? | Where to Get |
|-----|---------|-----------|--------------|
| **Moralis** | Blockchain data | Yes | https://admin.moralis.io/ |
| **Browser Cash** | Remote browsers | Yes (for scraping) | https://browsercash.io |
| **Agent Cash** | Token identification | Yes (for scraping) | https://browsercash.io |
| **Solana Private Key** | Trading | Yes (for trading) | Your wallet |

### File Locations

```
.env (project root)
├── BROWSER_CASH_API_KEY=...
├── AGENT_CASH_API_KEY=...
├── SOLANA_PRIVATE_KEY=...
└── MILAN_HOST=gcp-usc1-1.milan-taurine.tera.space

coin-ed/scrapper_and_analysis/.env
└── MORALIS_API_KEY=...
```

### Security Rules

- ✅ `.env` files are in `.gitignore` (NEVER committed)
- ✅ `.env.example` files are committed (safe templates)
- ✅ No hardcoded API keys in source code
- ✅ Use environment variables only

---

## 📊 Complete Workflow (Step by Step)

### Daily Usage

1. **Delete old data:**
   ```bash
   echo "[]" > scraped_posts.json
   ```

2. **Scrape Reddit (opens 3 tabs):**
   ```bash
   python main.py
   ```
   - Wait for completion (~30 minutes for past week)
   - Output: `scraped_posts.json` (890+ posts)

3. **Analyze sentiment:**
   ```bash
   cd sentiment_analysis
   python sentiment.py
   ```
   - Output: `sentiment.json`

4. **Fetch blockchain data:**
   ```bash
   cd ../coin-ed/scrapper_and_analysis
   python convert_to_coin_data.py
   ```
   - Output: `public/coin-data.json` (with real prices)

5. **View in dashboard:**
   ```bash
   cd ..
   npm start
   ```
   - Open: http://localhost:4200
   - See live prices and sentiment

6. **Trade (optional):**
   ```bash
   cd ../..
   python test_buy_hege.py  # Example
   ```

---

## 🎯 Key Technologies

### Backend (Python)
- **Browser Cash** - Remote browser automation
- **Playwright** - Browser control via CDP
- **Threading** - Parallel subreddit scraping
- **Requests** - API calls
- **Solana Web3.py** - Blockchain interaction

### Frontend (Angular)
- **Angular 20** - Latest framework
- **TypeScript** - Type safety
- **Chart.js** - Price visualizations
- **Signals** - Reactive state management
- **Standalone components** - Modern architecture

### APIs
- **DexScreener** - Free Solana token data
- **Moralis** - Multi-chain blockchain data
- **Jupiter** - Solana DEX aggregator
- **PumpPortal** - pump.fun token data
- **Browser Cash Agent** - AI token identification

---

## 📁 File Structure Summary

```
codejam2025/
├── main.py                    # ⭐ STEP 1: Scraper (3 tabs)
├── scraped_posts.json         # Output from main.py
├── sentiment_analysis/
│   ├── sentiment.py           # ⭐ STEP 2: Sentiment analysis
│   └── sentiment.json         # Output
├── coin-ed/
│   ├── scrapper_and_analysis/
│   │   ├── convert_to_coin_data.py  # ⭐ STEP 3: Blockchain data
│   │   ├── .env               # Moralis API key (not committed)
│   │   └── .env.example       # Template
│   ├── public/
│   │   └── coin-data.json     # Final output for frontend
│   └── src/app/               # ⭐ STEP 4: Angular dashboard
├── src/
│   ├── jupiter_client.py      # ⭐ STEP 5: Trading
│   ├── reddit_scraper.py      # Scraping logic
│   ├── agent_client.py        # AI token identification
│   └── browser_cash_client.py # Browser automation
├── .env                       # API keys (not committed)
└── .env.example               # Template
```

---

## 🎉 Summary

Your **Coin'ed** project is a **complete end-to-end pipeline**:

1. ✅ **Scrapes** Reddit with 3 parallel browsers (890+ posts)
2. ✅ **Analyzes** sentiment with AI
3. ✅ **Fetches** real blockchain data (prices, logos, addresses)
4. ✅ **Displays** in a beautiful Angular dashboard
5. ✅ **Trades** automatically on Solana (pending DNS fix)

**All data flows automatically from Reddit → Sentiment → Blockchain → Dashboard → Trading!**

🚀 **Built for CodeJam 2025** - A professional-grade crypto sentiment analysis and trading platform!

