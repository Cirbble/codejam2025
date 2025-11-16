# Moralis API Integration Guide - Solana Edition

## Overview
The `convert_to_coin_data.py` script integrates with **Moralis Web3 Data API** and **DexScreener API** to fetch real-time Solana token metadata including:
- ✅ Token contract address (Solana mint address)
- ✅ Current price in USD (from Solana DEXs)
- ✅ 24-hour price change
- ✅ Token logo/image
- ✅ Token decimals
- ✅ Liquidity data
- ✅ DEX information

## 🔑 API Key Setup

### Step 1: Create .env File

```bash
cd coin-ed/scrapper_and_analysis
cp .env.example .env
```

### Step 2: Add Your Moralis API Key

Edit `.env` and add your key:
```bash
MORALIS_API_KEY=your_actual_api_key_here
```

**Get your API key from:** https://admin.moralis.io/

### Step 3: Never Commit .env

The `.env` file is already in `.gitignore` - it will NEVER be pushed to GitHub.
**Only commit `.env.example`** which doesn't contain secrets.

## Features Added

### 1. Solana-First Search Strategy
The script **prioritizes Solana** since most meme coins are on Solana:
1. Searches Solana first using DexScreener API
2. Falls back to Moralis Solana API if needed  
3. If not found, tries Ethereum, BSC, and Polygon

### 2. DexScreener Integration (Primary)
- **Free API** - No key needed
- **Excellent Solana coverage** - Aggregates all Solana DEXs
- **Real-time prices** from Raydium, Orca, Jupiter, etc.
- **Token logos** and metadata
- **Liquidity data** to ensure valid tokens

### 3. Moralis as Fallback
- Used if DexScreener doesn't find the token
- Supports both Solana and EVM chains
- Requires API key (stored in .env)

## Supported Chains

According to Moralis documentation:

| Chain | ID | Support Level |
|-------|----|----|
| **Solana Mainnet** | `solana` | ✅ PRIMARY (via DexScreener + Moralis) |
| Ethereum | `0x1` | ✅ Fallback |
| BSC | `0x38` | ✅ Fallback |
| Polygon | `0x89` | ✅ Fallback |

## Output Format

The enhanced `coin-data.json` now includes:

```json
{
  "id": "hege",
  "name": "HEGE",
  "symbol": "HEGE",
  "address": "0x...",              // NEW: Token contract address
  "price": 0.00000123,             // NEW: Real price from Moralis
  "balance": 813008.13,            // Calculated based on price
  "decimals": 18,                  // NEW: Token decimals
  "logo": "https://...",           // NEW: Token logo URL
  "chain": "0x1",                  // NEW: Blockchain chain ID
  "changePercentage": 0.0523,      // NEW: Real 24h change
  "feedback": "Trending...",
  "raw_sentiment_score": 0.125,
  "aggregate_sentiment_score": 0.149,
  "engagement_score": 0.181,
  "confidence": 75,
  "recommendation": "BUY"
}
```

## Usage

### Setup (First Time Only)

1. **Install dependencies:**
   ```bash
   pip3 install requests python-dotenv
   ```

2. **Create .env file:**
   ```bash
   cd coin-ed/scrapper_and_analysis
   cp .env.example .env
   ```

3. **Add your Moralis API key to .env:**
   ```bash
   MORALIS_API_KEY=your_key_here
   ```

### Running the Script

```bash
cd coin-ed/scrapper_and_analysis
python3 convert_to_coin_data.py
```

### What Happens
1. Script reads `.env` file for API key
2. Reads `sentiment.json` with token mentions
3. For each token:
   - **First**: Searches Solana via DexScreener (free, no key needed)
   - **Then**: Tries Moralis Solana API (if DexScreener fails)
   - **Fallback**: Tries Ethereum, BSC, Polygon
4. Fetches token metadata, price, and logo
5. Combines with sentiment data
6. Outputs to `public/coin-data.json`

### Output Example
```
=== Fetching Token Metadata from Moralis ===

Processing: PAWS
  Searching for PAWS on Solana via DexScreener...
  ✓ Found: PAWS on Solana at $0.00002600
  ✓ Logo: https://cdn.dexscreener.com/...

Processing: KENDU
  Searching for KENDU on Solana via DexScreener...
  ✓ Found: Kendu on Solana at $0.00014000

=== Conversion Complete ===
Total unique coins: 14
Tokens found on-chain: 12/14 ✅

Top 5 coins by sentiment:
1. PAWS: Sentiment 1.0 | Confidence: 87% | BUY | 
   Price: $0.00002600 | Address: PAWSxhjT...Vgn6ZQ
   Logo: ✓
```

## API Details

### Moralis API Key
Stored in script: `MORALIS_API_KEY`

Already configured with your key:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Endpoints Used

#### 1. Search Token by Symbol
```
POST https://deep-index.moralis.io/api/v2.2/erc20/metadata/symbols
```
Searches for tokens by symbol across EVM chains.

#### 2. Get Token Price
```
GET https://deep-index.moralis.io/api/v2.2/erc20/{address}/price
```
Fetches current USD price and 24h change.

### Chain IDs
- `0x1` - Ethereum Mainnet
- `0x38` - Binance Smart Chain
- `0x89` - Polygon
- `0xa4b1` - Arbitrum
- `solana` - Solana (limited support)

## Limitations

### 1. Not All Tokens Are Found
- Many meme coins are on Solana or small DEXs
- Moralis may not index all tokens
- Script falls back to defaults if not found

### 2. Solana Tokens
- Limited support for Solana tokens in Moralis
- Consider integrating Jupiter API for better Solana coverage

### 3. Rate Limiting
- Free tier: Limited requests per minute
- Script includes retry logic and delays
- Consider caching results for production

## For Solana Tokens

Most meme coins mentioned in your sentiment data are likely on Solana. To get better coverage:

### Option 1: Use Jupiter API (Recommended for Solana)
```python
import requests

def get_solana_token_info(symbol: str):
    """Get Solana token info from Jupiter"""
    url = f"https://api.jup.ag/price/v2?ids={symbol}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('data', {}).get(symbol)
    return None
```

### Option 2: Use DexScreener API
```python
def get_token_from_dexscreener(symbol: str):
    """Search tokens on DexScreener"""
    url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        pairs = data.get('pairs', [])
        if pairs:
            return pairs[0]  # Return first match
    return None
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'requests'"
**Solution:**
```bash
pip3 install requests
```

### Issue: All tokens show "N/A" for address
**Possible causes:**
1. Tokens are on Solana (not well-supported by Moralis EVM API)
2. Tokens are too new or unlisted
3. API key issues

**Solutions:**
- Check if tokens are Solana-based
- Try DexScreener or Jupiter APIs
- Verify API key is valid

### Issue: Rate limit errors
**Solution:**
- Add delays between requests (already implemented)
- Upgrade Moralis plan
- Cache results locally

## Frontend Integration

The frontend automatically uses the new fields:

```typescript
// In data.service.ts
const coin: Coin = {
  id: data.id,
  name: data.name,
  symbol: data.symbol,
  address: data.address,        // Contract address
  price: data.price,            // Real price
  logo: data.logo,              // Token logo
  chain: data.chain,            // Blockchain
  changePercentage: data.changePercentage  // 24h change
};
```

Logo display:
```html
<!-- In coin-card.component.html -->
<img *ngIf="coin.logo" [src]="coin.logo" alt="{{coin.name}} logo">
```

## Next Steps

1. **Add Manual Token Mapping**
   Create a mapping file for known Solana tokens:
   ```json
   {
     "HEGE": {
       "address": "...",
       "price": 0.00000123,
       "logo": "https://..."
     }
   }
   ```

2. **Integrate Jupiter/DexScreener**
   For better Solana token support

3. **Add Caching**
   Cache API results to avoid repeated calls:
   ```python
   import json
   
   CACHE_FILE = "token_cache.json"
   
   def load_cache():
       try:
           with open(CACHE_FILE, 'r') as f:
               return json.load(f)
       except:
           return {}
   
   def save_cache(cache):
       with open(CACHE_FILE, 'w') as f:
           json.dump(cache, f)
   ```

4. **Add Price History**
   Use Moralis historical price API for charts

## Resources

- [Moralis Documentation](https://docs.moralis.com/web3-data-api/evm/reference)
- [Moralis Token API](https://docs.moralis.com/web3-data-api/evm/reference/get-token-price)
- [Jupiter API (Solana)](https://station.jup.ag/docs/apis/price-api)
- [DexScreener API](https://docs.dexscreener.com/)

## Support

If you need help with:
- Additional API integrations
- Custom token mappings
- Price feed setup
- Frontend display of logos/metadata

Let me know and I can help implement it!

