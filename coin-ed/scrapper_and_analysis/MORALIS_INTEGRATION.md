# Moralis API Integration Guide

## Overview
The `convert_to_coin_data.py` script now integrates with Moralis Web3 Data API to fetch real-time token metadata including:
- ✅ Token contract address
- ✅ Current price in USD
- ✅ 24-hour price change
- ✅ Token logo/image
- ✅ Token decimals
- ✅ Blockchain chain information

## Features Added

### 1. Automatic Token Lookup
The script automatically searches for each token mentioned in sentiment analysis across multiple blockchains:
- Ethereum (0x1)
- Binance Smart Chain (0x38)
- Polygon (0x89)
- Solana (experimental support)

### 2. Real Price Data
Instead of using default prices, the script fetches:
- Current USD price
- 24-hour percentage change
- Calculated balance based on $1000 portfolio value

### 3. Token Logos
Fetches official token logos from Moralis when available for display in the frontend.

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

### Basic Usage
```bash
cd coin-ed/scrapper_and_analysis
python3 convert_to_coin_data.py
```

### What Happens
1. Script reads `sentiment.json`
2. For each token found:
   - Searches Ethereum mainnet
   - If not found, tries BSC
   - If not found, tries Polygon
   - If not found, tries Solana
3. Fetches token metadata and price
4. Combines with sentiment data
5. Outputs to `public/coin-data.json`

### Output Example
```
=== Fetching Token Metadata from Moralis ===

Processing: HEGE
  Searching for HEGE on chain 0x1...
  ✓ Found: Hedgehog in the fog at $0.00000123
  ✓ Logo: https://cdn.moralis.io/...

Processing: KENDU
  Searching for KENDU on chain 0x1...
  Searching for KENDU on chain 0x38...
  ✗ Not found in Moralis - using defaults

=== Conversion Complete ===
Total unique coins: 14
Tokens found on-chain: 3/14

Top 5 coins by sentiment:
1. HEGE: Sentiment 0.832 | Confidence: 74% | BUY | Price: $0.00000123 | Address: 0x1234...
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

