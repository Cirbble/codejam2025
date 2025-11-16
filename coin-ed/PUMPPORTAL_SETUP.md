# PumpPortal Integration Setup

## Overview
The website is now integrated with PumpPortal API to fetch real-time token prices and information.

## API Documentation
- Base URL: `https://pumpportal.fun/api`
- Documentation: https://pumpportal.fun/

## How to Get Token Prices

### 1. Find the Token Mint Address
To get price data for HEGE or any token, you need its Solana mint address:
- Visit https://pump.fun and search for "HEGE"
- Or check Solscan: https://solscan.io
- Copy the token's mint address (contract address)

### 2. Add Token Address to Configuration
Edit `coin-ed/src/app/config/token-addresses.ts`:

```typescript
export const TOKEN_ADDRESSES: Record<string, string> = {
  'HEGE': 'YOUR_HEGE_MINT_ADDRESS_HERE',
  // Add more tokens as needed
};
```

### 3. Fetch Prices
The system will automatically fetch prices when:
- The dashboard loads
- You click "Refresh Prices" (if implemented)
- The scraper is enabled (can be configured)

## API Endpoints Used

### Get Token Information
```
GET https://pumpportal.fun/api/data/account/{mint_address}
```

Returns:
- Current price (calculated from reserves)
- Market cap
- Total supply
- Token metadata
- Social links
- And more...

## Price Calculation
Price is calculated from the bonding curve reserves:
```
price_in_SOL = virtual_sol_reserves / virtual_token_reserves
price_in_USD = price_in_SOL * SOL_price_USD
```

Or use the market cap method:
```
price_in_USD = usd_market_cap / total_supply
```

## Example: Getting HEGE Price

1. Find HEGE mint address (example placeholder):
   ```
   HEGExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

2. Make API call:
   ```
   GET https://pumpportal.fun/api/data/account/HEGExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

3. Response will include:
   ```json
   {
     "symbol": "HEGE",
     "name": "Hege",
     "usd_market_cap": 1234567.89,
     "total_supply": 1000000000,
     "virtual_sol_reserves": 123.45,
     "virtual_token_reserves": 987654321,
     ...
   }
   ```

4. Calculate price:
   ```
   price = 1234567.89 / 1000000000 = $0.00123456789
   ```

## Testing the Integration

1. Open browser console (F12)
2. Click on HEGE coin in the dashboard
3. Check console logs for:
   - "Fetching price for HEGE from PumpPortal..."
   - Price data output
   - Any errors

## Historical Price Data

Note: PumpPortal API doesn't provide direct historical price endpoints. For historical data, you would need to:
- Store prices over time in your own database
- Use trade history to reconstruct price movements
- Integrate with other APIs like CoinGecko or DexScreener

## Troubleshooting

### "No token address configured"
- Add the token's mint address to `token-addresses.ts`

### "Could not fetch price"
- Check if the mint address is correct
- Verify the token exists on pump.fun
- Check browser console for CORS or network errors

### CORS Issues
If you encounter CORS errors, you may need to:
- Use a proxy server
- Make requests from backend instead of frontend
- Contact PumpPortal for API access

## Next Steps

1. Find and add HEGE's actual mint address
2. Test the integration
3. Add automatic price refresh (every 30 seconds)
4. Store historical prices in a database
5. Add price charts using the historical data
