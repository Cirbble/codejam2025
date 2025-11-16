# Scrapper and Analysis Tools

This folder contains scripts for scraping cryptocurrency mentions from social media and analyzing sentiment.

## 🔐 Security - API Keys

**IMPORTANT:** Never commit API keys to GitHub!

### Setup .env File

1. Copy the example file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your keys:
   ```bash
   MORALIS_API_KEY=your_actual_key_here
   ```

3. The `.env` file is already in `.gitignore` - it will never be committed.

### Files:
- ✅ `.env.example` - Template (commit this)
- ❌ `.env` - Contains secrets (NEVER commit this)

## 📁 Files

### Scripts
- `sentiment.py` - Analyzes sentiment from scraped Reddit posts
- `convert_to_coin_data.py` - Converts sentiment data to coin metadata with real prices
- `scraped_posts.json` - Raw scraped social media posts
- `sentiment.json` - Analyzed sentiment scores

### Documentation
- `how_to_use.md` - Usage instructions
- `MORALIS_INTEGRATION.md` - API integration details
- `.env.example` - Environment variable template

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install requests python-dotenv
```

### 2. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env and add your Moralis API key
```

### 3. Run Sentiment Analysis
```bash
python3 sentiment.py
```

### 4. Convert to Coin Data with Real Prices
```bash
python3 convert_to_coin_data.py
```

This will:
- Search for tokens on Solana (using DexScreener API - free!)
- Fetch real prices, addresses, and logos
- Combine with sentiment analysis
- Output to `../public/coin-data.json`

## 🌐 APIs Used

### DexScreener API (Primary for Solana)
- **Free** - No API key needed
- Aggregates all Solana DEXs
- Real-time prices and liquidity
- Token logos and metadata

### Moralis API (Fallback & EVM chains)
- Requires API key (in .env)
- Supports Solana, Ethereum, BSC, Polygon
- Token metadata and prices

## 🔒 Security Best Practices

1. ✅ Always use `.env` for API keys
2. ✅ Add `.env` to `.gitignore`
3. ✅ Commit `.env.example` without real keys
4. ✅ Never hardcode API keys in scripts
5. ❌ Never commit `.env` to git
6. ❌ Never share API keys in chat/email

## 📊 Output Format

The `convert_to_coin_data.py` script generates `coin-data.json` with:

```json
{
  "id": "paws",
  "name": "PAWS",
  "symbol": "PAWS",
  "address": "PAWSxhjT...Vgn6ZQ",  // Real Solana address
  "price": 0.000026,                // Real price from DEX
  "balance": 38461538.46,
  "decimals": 9,                    // Solana standard
  "logo": "https://...",            // Token logo
  "chain": "solana",
  "changePercentage": -0.0101,      // 24h change
  "confidence": 87,
  "recommendation": "BUY",
  "sentiment": { ... }
}
```

## 🛠️ Troubleshooting

### "MORALIS_API_KEY not found in .env file"
- Make sure you created `.env` file
- Make sure you added `MORALIS_API_KEY=your_key` to it
- Check the file is in `scrapper_and_analysis/` folder

### Tokens not found
- Most meme coins are on Solana - script will find them!
- DexScreener has excellent Solana coverage
- If still not found, token may be too new/unlisted

### Rate limiting
- DexScreener is free and has generous limits
- Moralis free tier has limits - script includes retry logic
- Consider adding delays if hitting limits

## 📚 Documentation

See `MORALIS_INTEGRATION.md` for detailed API integration documentation.

## 🤝 Contributing

When adding new features:
1. Never commit API keys
2. Update `.env.example` if adding new environment variables
3. Document any new APIs in `MORALIS_INTEGRATION.md`

