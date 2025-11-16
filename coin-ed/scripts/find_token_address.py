#!/usr/bin/env python3
"""
Script to find Solana token addresses by name
Searches multiple sources: DexScreener, Jupiter, etc.
"""

import requests
import json
import sys

def search_dexscreener(token_name):
    """Search DexScreener for token address"""
    print(f"\n🔍 Searching DexScreener for {token_name}...")
    
    try:
        url = f'https://api.dexscreener.com/latest/dex/search?q={token_name}'
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('pairs'):
            solana_pairs = [p for p in data['pairs'] if 'solana' in p.get('chainId', '').lower()]
            
            if solana_pairs:
                print(f"✅ Found {len(solana_pairs)} Solana pair(s) for {token_name}:")
                
                for i, pair in enumerate(solana_pairs[:3], 1):  # Show top 3
                    base_token = pair.get('baseToken', {})
                    quote_token = pair.get('quoteToken', {})
                    
                    print(f"\n  Option {i}:")
                    print(f"    Token: {base_token.get('name')} ({base_token.get('symbol')})")
                    print(f"    Address: {base_token.get('address')}")
                    print(f"    Pair: {pair.get('pairAddress')}")
                    print(f"    DEX: {pair.get('dexId')}")
                    print(f"    Price USD: ${pair.get('priceUsd', 'N/A')}")
                    print(f"    Liquidity: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
                
                return solana_pairs[0].get('baseToken', {}).get('address')
            else:
                print(f"❌ No Solana pairs found for {token_name}")
        else:
            print(f"❌ No results found for {token_name}")
            
    except Exception as e:
        print(f"❌ Error searching DexScreener: {e}")
    
    return None

def search_jupiter(token_name):
    """Search Jupiter token list"""
    print(f"\n🔍 Searching Jupiter token list for {token_name}...")
    
    try:
        url = 'https://token.jup.ag/all'
        response = requests.get(url, timeout=10)
        tokens = response.json()
        
        # Search for matching tokens
        matches = [t for t in tokens if token_name.lower() in t.get('symbol', '').lower() 
                   or token_name.lower() in t.get('name', '').lower()]
        
        if matches:
            print(f"✅ Found {len(matches)} match(es) in Jupiter:")
            
            for i, token in enumerate(matches[:3], 1):
                print(f"\n  Option {i}:")
                print(f"    Name: {token.get('name')}")
                print(f"    Symbol: {token.get('symbol')}")
                print(f"    Address: {token.get('address')}")
                print(f"    Decimals: {token.get('decimals')}")
            
            return matches[0].get('address')
        else:
            print(f"❌ No matches found in Jupiter token list")
            
    except Exception as e:
        print(f"❌ Error searching Jupiter: {e}")
    
    return None

def main():
    if len(sys.argv) > 1:
        token_name = ' '.join(sys.argv[1:])
    else:
        token_name = input("Enter token name to search: ").strip()
    
    if not token_name:
        print("❌ Please provide a token name")
        return
    
    print(f"\n{'='*60}")
    print(f"Searching for: {token_name}")
    print(f"{'='*60}")
    
    # Try DexScreener first (usually has pump.fun tokens)
    address = search_dexscreener(token_name)
    
    # If not found, try Jupiter
    if not address:
        address = search_jupiter(token_name)
    
    # Print final result
    print(f"\n{'='*60}")
    if address:
        print(f"✅ FOUND TOKEN ADDRESS!")
        print(f"\nAdd this to coin-ed/src/app/config/token-addresses.ts:")
        print(f"\n  '{token_name.upper()}': '{address}',")
        print(f"\n{'='*60}")
    else:
        print(f"❌ Could not find token address for {token_name}")
        print(f"\nTry searching manually:")
        print(f"  - https://pump.fun (search for {token_name})")
        print(f"  - https://solscan.io (search for {token_name})")
        print(f"  - https://dexscreener.com (search for {token_name})")
        print(f"\n{'='*60}")

if __name__ == "__main__":
    main()
