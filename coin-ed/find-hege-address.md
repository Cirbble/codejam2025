# How to Find HEGE Token Address

Since you only have the name "HEGE", here are the ways to find its Solana mint address:

## Method 1: Check pump.fun (Recommended)
1. Go to https://pump.fun
2. Search for "HEGE" in the search bar
3. Click on the HEGE token
4. The URL will contain the mint address, or it will be displayed on the page
5. Copy the long alphanumeric string (the mint address)

## Method 2: Check Solscan
1. Go to https://solscan.io
2. Search for "HEGE" 
3. Look for the token in the results
4. Click on it to see the token address

## Method 3: Check DexScreener
1. Go to https://dexscreener.com
2. Search for "HEGE Solana" or just "HEGE"
3. Click on the token pair
4. The contract address will be shown

## Method 4: Check the Reddit Post
Since the HEGE data came from r/SatoshiStreetBets, you could:
1. Go to the original Reddit post
2. Look in comments for the contract address
3. Check if there's a website link that shows the address

## Method 5: Use a Script to Search
I can create a Python script that searches multiple sources:

```python
import requests

def search_hege():
    # Try DexScreener API
    try:
        response = requests.get('https://api.dexscreener.com/latest/dex/search?q=HEGE')
        data = response.json()
        
        if data.get('pairs'):
            for pair in data['pairs']:
                if 'solana' in pair.get('chainId', '').lower():
                    print(f"Found HEGE on Solana:")
                    print(f"Token Address: {pair.get('baseToken', {}).get('address')}")
                    print(f"Pair: {pair.get('pairAddress')}")
                    print(f"DEX: {pair.get('dexId')}")
                    return pair.get('baseToken', {}).get('address')
    except Exception as e:
        print(f"Error searching: {e}")
    
    return None

if __name__ == "__main__":
    address = search_hege()
    if address:
        print(f"\nAdd this to token-addresses.ts:")
        print(f"'HEGE': '{address}',")
    else:
        print("Could not find HEGE address automatically")
```

## What the Address Looks Like
A Solana token address looks like this:
```
HEGExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
It's typically 32-44 characters long, containing letters and numbers.

## Once You Have the Address
Add it to `coin-ed/src/app/config/token-addresses.ts`:

```typescript
export const TOKEN_ADDRESSES: Record<string, string> = {
  'HEGE': 'paste_the_address_here',
};
```

Then click "Refresh Prices" in the app!

## Alternative: If HEGE is Not on pump.fun
If HEGE is not a pump.fun token, you'll need to use a different API:
- Jupiter API (for Solana tokens)
- CoinGecko API
- DexScreener API

Let me know if you need help with any of these methods!
