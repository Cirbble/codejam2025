# Backend Console Logging Guide

## Overview
The backend now shows detailed, real-time progress when processing scraped data. This document explains what you'll see in the backend console when the web scraping completes.

## What You'll See

### 1. When Scraping Completes
```
Scraper process exited with code 0
✅ Scraping complete - processing data pipeline...
⚙️  Running sentiment analysis on scraped posts (trigger: process-exit)...
```

### 2. Sentiment Analysis Phase
```
============================================================
🧠 SENTIMENT ANALYSIS STARTING
============================================================
📂 Input file: /path/to/scraped_posts.json
📂 Output file: /path/to/sentiment.json
📊 Total posts loaded: 47

🔍 Processing post 1/47 - Token: PEP
   💬 Comments analyzed: 12
   📈 Raw sentiment: 0.753
   ✅ Aggregate sentiment: 0.821
   ✅ Engagement score: 0.654

🔍 Processing post 2/47 - Token: PAWS
   💬 Comments analyzed: 8
   📈 Raw sentiment: 0.682
   ✅ Aggregate sentiment: 0.741
   ✅ Engagement score: 0.589

⏭️  Skipping post 15/47 (ID: 342) - No token name

... (continues for all posts)

============================================================
✅ SENTIMENT ANALYSIS COMPLETE
============================================================
📂 Output: /path/to/sentiment.json
📊 Total posts processed: 43
⏭️  Posts skipped (no token): 4
🪙 Unique tokens found: 12
   Tokens: BIOK, GRASS, KENDU, KTA, MEWC, OBEY, PAWS, PEP, RAWW, SWELL, TAP, TRX
============================================================
```

### 3. API Token Metadata Phase
```
============================================================
🔄 CONVERTING SENTIMENT DATA TO COIN DATA
============================================================
📂 Input: /path/to/sentiment.json
📂 Output: /path/to/coin-data.json
✅ Cleared previous coin-data.json
📊 Loaded 43 posts with sentiment scores
🪙 Found 12 unique tokens
   Tokens: BIOK, GRASS, KENDU, KTA, MEWC, OBEY, PAWS, PEP, RAWW, SWELL, TAP, TRX

============================================================
🌐 FETCHING TOKEN METADATA FROM APIs
============================================================

[1/12] 🪙 Processing: PEP
   📝 Posts about this token: 5
   📊 Avg Raw Sentiment: 0.745
   📊 Avg Aggregate Sentiment: 0.823
   📊 Avg Engagement: 0.641
   💬 Total comments: 47
   🎯 Confidence: 82% → BUY
   🌐 Fetching metadata from APIs...

🔍 Searching for token: PEP on chain: solana
   🔍 Searching DexScreener for PEP on Solana...
   📡 DexScreener API Status: 200
   📊 Found 3 Solana pairs
   💰 Price from DexScreener: $0.00251900
   📈 24h Change: -0.01%
   📍 Token Address: GJAFwWjJ3vnTsrQVabjBVK2TYB1YtRCQXRDfDgUnpump
   🔄 No logo from DexScreener, trying Jupiter...
   🪐 Checking Jupiter token list for PEP logo...
   ✅ Found logo in Jupiter: https://cf-ipfs.com/ipfs/QmR8YSy...
   
   ✅ Found: PEP on Solana
   💵 Price: $0.00251900
   📈 24h Change: -0.01%
   📍 Address: GJAFwWjJ3vnTsrQVabjBVK2TYB1YtRCQXRDfDgUnpump
   🖼️  Logo: https://cf-ipfs.com/ipfs/QmR8YSy...

[2/12] 🪙 Processing: PAWS
   📝 Posts about this token: 3
   📊 Avg Raw Sentiment: 0.721
   📊 Avg Aggregate Sentiment: 0.798
   📊 Avg Engagement: 0.612
   💬 Total comments: 31
   🎯 Confidence: 79% → BUY
   🌐 Fetching metadata from APIs...
   
   ✅ Found: PAWS on Solana
   💵 Price: $0.00002600
   📈 24h Change: -0.99%
   📍 Address: 2qEHjDLDLbuBgRYvsxhc5D6uDWAivNFZGan56P1tpump
   🖼️  Logo: https://dd.dexscreener.com/ds-data/tokens/...
   
[3/12] 🪙 Processing: UNKNOWN_TOKEN
   📝 Posts about this token: 1
   ...
   ❌ Token metadata not found - using defaults

... (continues for all tokens)
```

### 4. Final Summary
```
============================================================
✅ CONVERSION COMPLETE
============================================================
📂 Output: /path/to/public/coin-data.json
📊 Total coins: 12
🌐 Tokens found on-chain: 10/12
🖼️  Logos found: 9/12

🏆 Top 5 coins by sentiment:
   1. PEP
      Sentiment: 0.823 | Confidence: 82% | BUY
      Price: $0.00251900 | Address: GJAFwWjJ3v... | Logo: ✅
   2. PAWS
      Sentiment: 0.798 | Confidence: 79% | BUY
      Price: $0.00002600 | Address: 2qEHjDLDLb... | Logo: ✅
   3. MEWC
      Sentiment: 0.765 | Confidence: 76% | BUY
      Price: $0.00000634 | Address: MEWCRvqE5t... | Logo: ✅
   4. BIOK
      Sentiment: 0.712 | Confidence: 71% | HOLD
      Price: $0.00067510 | Address: BioKs7oWxH... | Logo: ✅
   5. KENDU
      Sentiment: 0.698 | Confidence: 69% | HOLD
      Price: $0.00014000 | Address: 6VVf4bUVQM... | Logo: ✅

📊 Recommendations:
   🟢 BUY:  5
   🟡 HOLD: 4
   🔴 SELL: 3
============================================================

📡 Broadcasted coin_data_updated to 1 client(s)
```

### 5. Frontend Update
```
🔄 Reloading coin data after coin_data_updated event
✅ Loaded 12 coins successfully
```

## What Each Symbol Means

### Status Icons
- `🧠` - Sentiment Analysis
- `🔄` - Conversion/Processing
- `🌐` - API Calls
- `🪙` - Cryptocurrency/Token
- `📡` - API Response
- `💰` - Price Data
- `🖼️` - Logo/Image
- `📍` - Address/Location
- `📈` - Chart/Statistics
- `💬` - Comments
- `✅` - Success
- `❌` - Failure/Not Found
- `⚠️` - Warning
- `⏭️` - Skipped
- `🎯` - Recommendation

### Recommendation Colors
- `🟢 BUY` - Confidence ≥ 75%
- `🟡 HOLD` - Confidence 55-74%
- `🔴 SELL` - Confidence < 55%

## API Call Flow

For each token, the system tries multiple sources in order:

1. **DexScreener** (Primary)
   - Free, no API key
   - Best for Solana tokens
   - Provides: Price, Address, Pairs, Liquidity

2. **Jupiter** (Logos)
   - Solana token list
   - Comprehensive logo database
   - Fallback if DexScreener has no logo

3. **Moralis** (Backup)
   - Requires API key
   - Multi-chain support
   - Provides: Metadata, Price, Decimals

## Troubleshooting

### If you see many `❌ Token metadata not found`
- Check if tokens are very new (not indexed yet)
- Verify Moralis API key is valid
- Check rate limits (Moralis free tier)

### If logos are missing (`Logo: ❌`)
- Jupiter token list may not have the logo
- DexScreener may not have indexed the token
- Token might be too new or low liquidity

### If prices show as $0.001 (default)
- Token not found on any DEX
- Very low liquidity
- Not yet indexed by DexScreener

## How to Run Manually

To test the pipeline manually:

```bash
# 1. Run sentiment analysis
cd coin-ed/scrapper_and_analysis
python3 sentiment.py

# 2. Run conversion
python3 convert_to_coin_data.py
```

## Environment Variables Required

Make sure these are set in `coin-ed/.env`:

```bash
MORALIS_API_KEY=your_api_key_here
```

## Expected Performance

- **Sentiment Analysis**: ~1-2 seconds per 10 posts
- **API Calls**: ~2-3 seconds per token
- **Total Pipeline**: ~30-60 seconds for 50 posts with 10 unique tokens

## Success Indicators

You know the pipeline worked if you see:
1. ✅ All three completion messages (Scraping → Sentiment → Conversion)
2. `coin_data_updated` broadcast message
3. No `❌ Error` messages in critical paths
4. Frontend shows updated coin list with new data

