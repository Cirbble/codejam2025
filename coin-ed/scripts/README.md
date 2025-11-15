# Token Address Finder Script

## Quick Start

Run the script to find HEGE's token address:

```bash
python find_token_address.py HEGE
```

Or run it interactively:

```bash
python find_token_address.py
# Then type: HEGE
```

## What It Does

The script searches multiple sources to find the Solana token address:
1. **DexScreener API** - Searches DEX pairs (includes pump.fun tokens)
2. **Jupiter Token List** - Searches verified Solana tokens

## Output

If found, you'll see:
```
✅ FOUND TOKEN ADDRESS!

Add this to coin-ed/src/app/config/token-addresses.ts:

  'HEGE': 'HEGExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
```

## Requirements

```bash
pip install requests
```

## If Not Found

If the script can't find HEGE automatically, search manually:
- https://pump.fun (search "HEGE")
- https://solscan.io (search "HEGE")  
- https://dexscreener.com (search "HEGE Solana")

## After Finding the Address

1. Copy the address
2. Open `coin-ed/src/app/config/token-addresses.ts`
3. Add the line:
   ```typescript
   'HEGE': 'paste_address_here',
   ```
4. Restart the dev server
5. Click "Refresh Prices" in the app

## Example for Other Tokens

```bash
python find_token_address.py BONK
python find_token_address.py WIF
python find_token_address.py "Dogwifhat"
```
