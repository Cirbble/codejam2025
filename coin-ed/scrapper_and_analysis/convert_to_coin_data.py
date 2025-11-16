import json
import os
import requests
import time
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Moralis API Configuration
MORALIS_API_KEY = os.getenv('MORALIS_API_KEY')
if not MORALIS_API_KEY:
    raise ValueError("MORALIS_API_KEY not found in .env file!")

MORALIS_BASE_URL = "https://solana-gateway.moralis.io"
MORALIS_EVM_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

def search_token_by_name(token_name: str, chain: str = "solana") -> Optional[Dict]:
    """
    Search for a token by name using Moralis API.
    Returns token metadata including address, price, and logo.

    Args:
        token_name: Name or symbol of the token
        chain: Chain ID (default: solana for Solana mainnet)
               Other options: 0x1 (Ethereum), 0x89 (Polygon), 0x38 (BSC)
    """
    try:
        print(f"\n🔍 Searching for token: {token_name} on chain: {chain}", flush=True)

        # For Solana, use Solana-specific endpoint
        if chain == "solana":
            return search_solana_token(token_name)

        # For EVM chains (Ethereum, BSC, Polygon, etc.)
        # First, try to search by symbol
        search_url = f"{MORALIS_EVM_BASE_URL}/erc20/metadata/symbols"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        params = {
            "chain": chain,
            "symbols": [token_name.upper()]
        }

        print(f"   🌐 Calling Moralis API: {search_url}", flush=True)
        response = requests.post(search_url, json=params, headers=headers)
        print(f"   📡 API Response Status: {response.status_code}", flush=True)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                token_info = data[0]
                address = token_info.get('address')

                print(f"   ✅ Token found! Address: {address}", flush=True)

                if address:
                    # Get token price
                    print(f"   💰 Fetching price data...", flush=True)
                    price_data = get_token_price(address, chain)

                    result = {
                        'address': address,
                        'name': token_info.get('name', token_name),
                        'symbol': token_info.get('symbol', token_name),
                        'decimals': token_info.get('decimals', 18),
                        'logo': token_info.get('logo'),
                        'thumbnail': token_info.get('thumbnail'),
                        'price_usd': price_data.get('usdPrice', 0) if price_data else 0,
                        'price_change_24h': price_data.get('24hrPercentChange') if price_data else 0,
                        'chain': chain
                    }

                    print(f"   💵 Price: ${result['price_usd']}", flush=True)
                    print(f"   🖼️  Logo: {'Found' if result['logo'] else 'Not found'}", flush=True)

                    return result
            else:
                print(f"   ⚠️ No results returned from API", flush=True)

        # If not found on current chain, try other chains
        # Priority: Solana > Ethereum > BSC > Polygon
        if chain == "solana":
            print(f"   🔄 Trying Ethereum...", flush=True)
            # Try Ethereum
            eth_result = search_token_by_name(token_name, "0x1")
            if eth_result:
                return eth_result

            print(f"   🔄 Trying BSC...", flush=True)
            # Try BSC (Binance Smart Chain)
            bsc_result = search_token_by_name(token_name, "0x38")
            if bsc_result:
                return bsc_result

            print(f"   🔄 Trying Polygon...", flush=True)
            # Try Polygon
            polygon_result = search_token_by_name(token_name, "0x89")
            if polygon_result:
                return polygon_result

        print(f"   ❌ Token {token_name} not found on any chain", flush=True)
        return None

    except Exception as e:
        print(f"   ❌ Error searching for token {token_name}: {str(e)}", flush=True)
        return None

def search_jupiter_token(token_symbol: str) -> Optional[Dict]:
    """
    Search for token in Jupiter token list to get logo.
    Jupiter has comprehensive Solana token metadata including logos.
    Uses static CDN to avoid DNS issues.
    """
    try:
        print(f"   🪐 Checking Jupiter token list for {token_symbol} logo...", flush=True)

        # Use GitHub raw content as alternative (Jupiter tokens are on GitHub)
        # Or use cached/local file approach
        jupiter_url = "https://cache.jup.ag/tokens"

        response = requests.get(jupiter_url, timeout=10)

        if response.status_code == 200:
            tokens = response.json()

            # Search by symbol
            for token in tokens:
                if token.get('symbol', '').upper() == token_symbol.upper():
                    logo_uri = token.get('logoURI')
                    if logo_uri:
                        print(f"   ✅ Found logo in Jupiter: {logo_uri[:60]}...", flush=True)
                        return {
                            'logo': logo_uri,
                            'address': token.get('address'),
                            'name': token.get('name'),
                            'symbol': token.get('symbol'),
                            'decimals': token.get('decimals', 9)
                        }

        print(f"   ⚠️ No logo found in Jupiter for {token_symbol}", flush=True)
        return None

    except Exception as e:
        print(f"   ⚠️ Jupiter lookup failed: {str(e)}", flush=True)
        return None

def search_solana_token(token_symbol: str) -> Optional[Dict]:
    """
    Search for a Solana token using DexScreener API (better Solana coverage than Moralis).
    DexScreener aggregates data from all Solana DEXs.
    Falls back to Jupiter for logos if DexScreener doesn't have them.
    """
    try:
        print(f"   🔍 Searching DexScreener for {token_symbol} on Solana...", flush=True)

        # DexScreener API - free, no API key needed, great Solana support
        search_url = f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}"

        headers = {
            "Accept": "application/json"
        }

        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"   📡 DexScreener API Status: {response.status_code}", flush=True)

        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])

            # Filter for Solana pairs
            solana_pairs = [p for p in pairs if p.get('chainId') == 'solana']

            print(f"   📊 Found {len(solana_pairs)} Solana pairs", flush=True)

            if solana_pairs:
                # Get the pair with highest liquidity
                best_pair = max(solana_pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0) or 0))

                base_token = best_pair.get('baseToken', {})
                price_usd = float(best_pair.get('priceUsd', 0))
                price_change_24h = float(best_pair.get('priceChange', {}).get('h24', 0) or 0)

                print(f"   💰 Price from DexScreener: ${price_usd}", flush=True)
                print(f"   📈 24h Change: {price_change_24h}%", flush=True)

                # Try manual logo mapping first (for well-known tokens)
                logo = MANUAL_LOGOS.get(token_symbol.upper())

                # If no manual mapping, try DexScreener
                if not logo:
                    logo = best_pair.get('info', {}).get('imageUrl')

                token_address = base_token.get('address', 'N/A')

                print(f"   📍 Token Address: {token_address}", flush=True)

                # Try multiple sources for logo (DexScreener -> Jupiter -> Moralis)
                if not logo:
                    print(f"   🔄 No logo from DexScreener, trying Jupiter...", flush=True)
                    jupiter_data = search_jupiter_token(token_symbol)
                    if jupiter_data:
                        logo = jupiter_data.get('logo')

                # If still no logo, try Moralis as last resort
                if not logo and token_address != 'N/A':
                    print(f"   🔄 No logo from Jupiter, trying Moralis...", flush=True)
                    moralis_logo = get_moralis_token_logo(token_address)
                    if moralis_logo:
                        logo = moralis_logo
                        print(f"  ✓ Found logo in Moralis!", flush=True)

                return {
                    'address': token_address,
                    'name': base_token.get('name', token_symbol),
                    'symbol': base_token.get('symbol', token_symbol),
                    'decimals': 9,  # Solana standard
                    'logo': logo,
                    'thumbnail': logo,
                    'price_usd': price_usd,
                    'price_change_24h': price_change_24h,
                    'chain': 'solana',
                    'dex': best_pair.get('dexId', 'unknown'),
                    'liquidity_usd': float(best_pair.get('liquidity', {}).get('usd', 0) or 0)
                }

        # Fallback: Try Moralis Solana API if DexScreener fails
        return search_solana_token_moralis(token_symbol)

    except Exception as e:
        print(f"  Error searching Solana token via DexScreener: {str(e)}", flush=True)
        # Try Moralis as fallback
        return search_solana_token_moralis(token_symbol)

# Manual logo mappings for well-known tokens (highest priority)
# Using CoinGecko CDN for reliable, high-quality logos
MANUAL_LOGOS = {
    'BTC': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png',
    'ETH': 'https://assets.coingecko.com/coins/images/279/large/ethereum.png',
    'SOL': 'https://assets.coingecko.com/coins/images/4128/large/solana.png',
    'USDC': 'https://assets.coingecko.com/coins/images/6319/large/USD_Coin_icon.png',
    'USDT': 'https://assets.coingecko.com/coins/images/325/large/Tether.png',
}

def get_moralis_token_logo(token_address: str) -> Optional[str]:
    """
    Get token logo from Moralis API by token address.
    """
    try:
        metadata_url = f"{MORALIS_BASE_URL}/token/mainnet/{token_address}/metadata"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

        response = requests.get(metadata_url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            logo = data.get('logoURI') or data.get('logo') or data.get('image')
            return logo

        return None

    except Exception:
        # Silently fail - logo is optional
        return None

def search_solana_token_moralis(token_symbol: str) -> Optional[Dict]:
    """
    Fallback: Search for a Solana token using Moralis Solana API.
    """
    try:
        print(f"  Trying Moralis Solana API for {token_symbol}...", flush=True)

        # Moralis Solana API endpoint for token metadata
        search_url = f"{MORALIS_BASE_URL}/token/mainnet/{token_symbol}/metadata"

        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

        response = requests.get(search_url, headers=headers)

        if response.status_code == 200:
            token_data = response.json()

            if token_data:
                # Get token price
                token_address = token_data.get('mint') or token_data.get('address')
                price_data = None

                if token_address:
                    price_data = get_solana_token_price(token_address)

                return {
                    'address': token_address or 'N/A',
                    'name': token_data.get('name', token_symbol),
                    'symbol': token_data.get('symbol', token_symbol),
                    'decimals': token_data.get('decimals', 9),
                    'logo': token_data.get('logoURI') or token_data.get('logo'),
                    'thumbnail': token_data.get('thumbnail'),
                    'price_usd': price_data.get('usdPrice', 0) if price_data else 0,
                    'price_change_24h': price_data.get('24hrPercentChange', 0) if price_data else 0,
                    'chain': 'solana'
                }

        print(f"  Moralis: token {token_symbol} not found on Solana", flush=True)
        return None

    except Exception as e:
        print(f"  Error with Moralis Solana API: {str(e)}", flush=True)
        return None

def get_solana_token_price(token_address: str) -> Optional[Dict]:
    """
    Get Solana token price using Moralis Solana API.
    """
    try:
        price_url = f"{MORALIS_BASE_URL}/token/mainnet/{token_address}/price"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }

        response = requests.get(price_url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Failed to get Solana price for {token_address[:10]}...: {response.status_code}", flush=True)
            return None

    except Exception as e:
        print(f"  Error getting Solana token price: {str(e)}", flush=True)
        return None

def get_token_price(token_address: str, chain: str = "0x1") -> Optional[Dict]:
    """
    Get current token price using Moralis API for EVM chains.

    Args:
        token_address: Contract address of the token
        chain: Chain ID
    """
    try:
        price_url = f"{MORALIS_EVM_BASE_URL}/erc20/{token_address}/price"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        params = {
            "chain": chain
        }

        response = requests.get(price_url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Failed to get price for {token_address}: {response.status_code}", flush=True)
            return None

    except Exception as e:
        print(f"  Error getting token price: {str(e)}", flush=True)
        return None

def get_token_metadata_with_retry(token_name: str, max_retries: int = 2) -> Optional[Dict]:
    """
    Get token metadata with retry logic and rate limiting.
    """
    for attempt in range(max_retries):
        result = search_token_by_name(token_name)
        if result:
            return result

        if attempt < max_retries - 1:
            # Wait before retrying to avoid rate limiting
            time.sleep(1)

    return None

def convert_sentiment_to_coin_data(input_file, output_file):
    """
    Convert sentiment.json to coin-data.json format.
    Combines duplicate coins by averaging values and merging comments.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, input_file)
    output_path = os.path.join(script_dir, '..', 'public', output_file)

    print(f"\n{'='*60}", flush=True)
    print(f"🔄 CONVERTING SENTIMENT DATA TO COIN DATA", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"📂 Input: {input_path}", flush=True)
    print(f"📂 Output: {output_path}", flush=True)

    # Ensure parent output directory exists and clear previous file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
      open(output_path, 'w').close()
      print(f"✅ Cleared previous coin-data.json", flush=True)
    except Exception as e:
      print(f"⚠️  Could not clear previous file: {e}", flush=True)

    # Read sentiment data
    # Read sentiment data
    with open(input_path, 'r', encoding='utf-8') as f:
        sentiment_data = json.load(f)

    print(f"📊 Loaded {len(sentiment_data)} posts with sentiment scores", flush=True)

    # Dictionary to group posts by token name
    coin_groups = {}

    for post in sentiment_data:
        token_name = post.get('token_name', 'UNKNOWN')

        if token_name not in coin_groups:
            coin_groups[token_name] = []

        coin_groups[token_name].append(post)

    print(f"🪙 Found {len(coin_groups)} unique tokens", flush=True)
    print(f"   Tokens: {', '.join(coin_groups.keys())}", flush=True)

    # Process each coin group
    coin_data = []

    print(f"\n{'='*60}", flush=True)
    print(f"🌐 FETCHING TOKEN METADATA FROM APIs", flush=True)
    print(f"{'='*60}", flush=True)

    for idx, (token_name, posts) in enumerate(coin_groups.items(), 1):
        print(f"\n[{idx}/{len(coin_groups)}] 🪙 Processing: {token_name}", flush=True)
        print(f"   📝 Posts about this token: {len(posts)}", flush=True)

        # Calculate averages
        avg_raw_sentiment = sum(p.get('raw_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_aggregate_sentiment = sum(p.get('aggregate_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_engagement = sum(p.get('engagement_score', 0.0) for p in posts) / len(posts)

        print(f"   📊 Avg Raw Sentiment: {avg_raw_sentiment:.3f}", flush=True)
        print(f"   📊 Avg Aggregate Sentiment: {avg_aggregate_sentiment:.3f}", flush=True)
        print(f"   📊 Avg Engagement: {avg_engagement:.3f}", flush=True)

        # Combine all comments from all posts
        all_comments = []
        for post in posts:
            post_comments = post.get('comments', [])
            if isinstance(post_comments, list):
                all_comments.extend(post_comments)

        # Remove duplicate comments and moderator messages
        unique_comments = []
        seen_comments = set()
        for comment in all_comments:
            # Skip moderator announcements
            if 'Moderator Announcement' in comment or 'I am a bot' in comment:
                continue
            # Skip duplicates
            comment_lower = comment.lower().strip()
            if comment_lower not in seen_comments:
                seen_comments.add(comment_lower)
                unique_comments.append(comment)

        print(f"   💬 Total comments: {len(unique_comments)}", flush=True)

        # Use the most recent post for main data
        latest_post = max(posts, key=lambda p: p.get('timestamp', ''))

        # Combine titles if multiple posts
        if len(posts) > 1:
            title = f"{latest_post.get('title', '')} (+{len(posts)-1} more posts)"
        else:
            title = latest_post.get('title', '')

        # Sum up engagement metrics
        total_upvotes = sum(p.get('upvotes_likes', 0) for p in posts)
        total_comments = len(unique_comments)

        # Calculate overall confidence score (0-100%)
        # Weight: 30% raw sentiment, 50% aggregate sentiment, 20% engagement
        normalized_raw = (avg_raw_sentiment + 1) / 2  # Convert from -1 to 1 scale to 0 to 1
        normalized_aggregate = (avg_aggregate_sentiment + 1) / 2
        normalized_engagement = avg_engagement  # Already 0-1

        confidence = (normalized_raw * 0.3) + (normalized_aggregate * 0.5) + (normalized_engagement * 0.2)
        confidence_percentage = round(confidence * 100)

        # Determine recommendation based on confidence
        if confidence_percentage >= 75:
            recommendation = "BUY"
        elif confidence_percentage >= 55:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        print(f"   🎯 Confidence: {confidence_percentage}% → {recommendation}", flush=True)

        # Fetch token metadata from Moralis API
        print(f"   🌐 Fetching metadata from APIs...", flush=True)
        token_metadata = get_token_metadata_with_retry(token_name)

        # Default values if API call fails
        token_address = "N/A"
        token_price = 0.001  # Default small price
        token_logo = None
        token_decimals = 18
        price_change_24h = 0
        chain_id = "0x1"

        if token_metadata:
            token_address = token_metadata.get('address', 'N/A')
            token_price = token_metadata.get('price_usd', 0.001)
            token_logo = token_metadata.get('logo') or token_metadata.get('thumbnail')
            token_decimals = token_metadata.get('decimals', 18)
            price_change_24h = token_metadata.get('price_change_24h', 0)
            chain_id = token_metadata.get('chain', 'solana')

            # Display chain name instead of ID
            chain_name = 'Solana' if chain_id == 'solana' else chain_id
            print(f"   ✅ Found: {token_metadata.get('name')} on {chain_name}", flush=True)
            print(f"   💵 Price: ${token_price:.8f}", flush=True)
            print(f"   📈 24h Change: {price_change_24h}%", flush=True)
            print(f"   📍 Address: {token_address}", flush=True)
            if token_logo:
                print(f"   🖼️  Logo: {token_logo[:60]}...", flush=True)
            else:
                print(f"   ⚠️  No logo found", flush=True)
        else:
            print(f"   ❌ Token metadata not found - using defaults", flush=True)

        # Calculate balance based on price (keep total value ~$1000)
        if token_price > 0:
            balance = 1000 / token_price
        else:
            balance = 1000000  # Default large balance for unknown tokens

        # Create combined coin entry
        coin_entry = {
            "id": token_name.lower(),
            "name": token_name,
            "symbol": token_name,
            "address": token_address,  # NEW: Token contract address
            "price": token_price,  # NEW: Real price from Moralis
            "balance": round(balance, 2),
            "decimals": token_decimals,  # NEW: Token decimals
            "logo": token_logo,  # NEW: Token logo URL
            "chain": chain_id,  # NEW: Blockchain chain ID
            "feedback": f"Trending on {latest_post.get('source', 'reddit')} ({len(posts)} posts)",
            "changePercentage": price_change_24h / 100 if price_change_24h else 0.0,  # NEW: Real 24h change
            "icon": token_name,
            "raw_sentiment_score": round(avg_raw_sentiment, 3),
            "aggregate_sentiment_score": round(avg_aggregate_sentiment, 3),
            "engagement_score": round(avg_engagement, 3),
            "source": latest_post.get('source', ''),
            "platform": latest_post.get('platform', ''),
            "title": title,
            "content": latest_post.get('content', '')[:500] if latest_post.get('content') else '',
            "author": latest_post.get('author', ''),
            "timestamp": latest_post.get('timestamp', ''),
            "post_age": latest_post.get('post_age', ''),
            "upvotes_likes": total_upvotes,
            "comment_count": total_comments,
            "comments": unique_comments,  # All unique comments combined
            "link": latest_post.get('link', ''),
            "post_count": len(posts),  # Track how many posts were combined
            "confidence": confidence_percentage,
            "recommendation": recommendation
        }

        coin_data.append(coin_entry)

    # Sort by aggregate sentiment score (highest first)
    coin_data.sort(key=lambda x: x['aggregate_sentiment_score'], reverse=True)

    # Write final coin data (overwrite)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coin_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}", flush=True)
    print(f"✅ CONVERSION COMPLETE", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"📂 Output: {output_path}", flush=True)
    print(f"📊 Total coins: {len(coin_data)}", flush=True)

    # Count tokens found vs not found
    found_count = sum(1 for c in coin_data if c['address'] != 'N/A')
    logo_count = sum(1 for c in coin_data if c.get('logo'))
    print(f"🌐 Tokens found on-chain: {found_count}/{len(coin_data)}", flush=True)
    print(f"🖼️  Logos found: {logo_count}/{len(coin_data)}", flush=True)

    print(f"\n🏆 Top 5 coins by sentiment:", flush=True)
    for i, coin in enumerate(coin_data[:5], 1):
        address_display = coin['address'][:10] + '...' if coin['address'] != 'N/A' else 'N/A'
        price_display = f"${coin['price']:.8f}" if coin['price'] < 1 else f"${coin['price']:.2f}"
        logo_status = "✅" if coin.get('logo') else "❌"
        print(f"   {i}. {coin['name']}", flush=True)
        print(f"      Sentiment: {coin['aggregate_sentiment_score']:.3f} | Confidence: {coin['confidence']}% | {coin['recommendation']}", flush=True)
        print(f"      Price: {price_display} | Address: {address_display} | Logo: {logo_status}", flush=True)

    # Show recommendation breakdown
    buy_count = sum(1 for c in coin_data if c['recommendation'] == 'BUY')
    hold_count = sum(1 for c in coin_data if c['recommendation'] == 'HOLD')
    sell_count = sum(1 for c in coin_data if c['recommendation'] == 'SELL')

    print(f"\n📊 Recommendations:", flush=True)
    print(f"   🟢 BUY:  {buy_count}", flush=True)
    print(f"   🟡 HOLD: {hold_count}", flush=True)
    print(f"   🔴 SELL: {sell_count}", flush=True)
    print(f"{'='*60}\n", flush=True)

if __name__ == "__main__":
    convert_sentiment_to_coin_data("sentiment.json", "coin-data.json")
