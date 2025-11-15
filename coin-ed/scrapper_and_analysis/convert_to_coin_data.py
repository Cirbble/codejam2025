import json
import os
import requests
import time
from typing import Dict, Optional

# Moralis API Configuration
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjY0YjRjNDBjLTNmNTktNGNmMy05ZDRiLTIxNDQxNTUwNDE4ZiIsIm9yZ0lkIjoiNDgxNTg5IiwidXNlcklkIjoiNDk1NDU3IiwidHlwZSI6IlBST0pFQ1QiLCJ0eXBlSWQiOiJlNmY4MWEwOS1iOTNiLTQ1ZGEtYmUwNC0yZDcwMDNmYmJlMmYiLCJpYXQiOjE3NjMyNTAzNjksImV4cCI6NDkxOTAxMDM2OX0.th7aW4mRImwelj-l_rAQJSMsG-B0LiTLdvVW53j0rfo"
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2.2"

def search_token_by_name(token_name: str, chain: str = "0x1") -> Optional[Dict]:
    """
    Search for a token by name using Moralis API.
    Returns token metadata including address, price, and logo.

    Args:
        token_name: Name or symbol of the token
        chain: Chain ID (default: 0x1 for Ethereum mainnet)
               Other options: 0x89 (Polygon), 0x38 (BSC), 0xa4b1 (Arbitrum), solana (Solana)
    """
    try:
        # For Solana, use different endpoint
        if chain == "solana":
            # Try to get token info for Solana
            # Note: Moralis Solana API has different structure
            # We'll search by symbol using the token endpoint
            return search_solana_token(token_name)

        # For EVM chains (Ethereum, BSC, Polygon, etc.)
        # First, try to search by symbol
        search_url = f"{MORALIS_BASE_URL}/erc20/metadata/symbols"
        headers = {
            "Accept": "application/json",
            "X-API-Key": MORALIS_API_KEY
        }
        params = {
            "chain": chain,
            "symbols": [token_name.upper()]
        }

        print(f"  Searching for {token_name} on chain {chain}...")
        response = requests.post(search_url, json=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                token_info = data[0]
                address = token_info.get('address')

                if address:
                    # Get token price
                    price_data = get_token_price(address, chain)

                    return {
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

        # If not found on current chain, try other chains
        if chain == "0x1":
            # Try BSC (Binance Smart Chain)
            bsc_result = search_token_by_name(token_name, "0x38")
            if bsc_result:
                return bsc_result

            # Try Polygon
            polygon_result = search_token_by_name(token_name, "0x89")
            if polygon_result:
                return polygon_result

            # Try Solana (most meme coins are on Solana)
            solana_result = search_token_by_name(token_name, "solana")
            if solana_result:
                return solana_result

        print(f"  Token {token_name} not found on chain {chain}")
        return None

    except Exception as e:
        print(f"  Error searching for token {token_name}: {str(e)}")
        return None

def search_solana_token(token_symbol: str) -> Optional[Dict]:
    """
    Search for a Solana token using Moralis Solana API.
    """
    try:
        # Moralis doesn't have great support for searching Solana tokens by symbol
        # We'll use a workaround by trying common token addresses
        # For now, return None and let it fall back to defaults
        # In a production system, you'd integrate with Jupiter or other Solana DEX aggregators

        print(f"  Searching for {token_symbol} on Solana (limited support)...")
        return None

    except Exception as e:
        print(f"  Error searching Solana token: {str(e)}")
        return None

def get_token_price(token_address: str, chain: str = "0x1") -> Optional[Dict]:
    """
    Get current token price using Moralis API.

    Args:
        token_address: Contract address of the token
        chain: Chain ID
    """
    try:
        price_url = f"{MORALIS_BASE_URL}/erc20/{token_address}/price"
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
            print(f"  Failed to get price for {token_address}: {response.status_code}")
            return None

    except Exception as e:
        print(f"  Error getting token price: {str(e)}")
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

    # Read sentiment data
    with open(input_path, 'r', encoding='utf-8') as f:
        sentiment_data = json.load(f)

    # Dictionary to group posts by token name
    coin_groups = {}

    for post in sentiment_data:
        token_name = post.get('token_name', 'UNKNOWN')

        if token_name not in coin_groups:
            coin_groups[token_name] = []

        coin_groups[token_name].append(post)

    # Process each coin group
    coin_data = []

    print("\n=== Fetching Token Metadata from Moralis ===")

    for token_name, posts in coin_groups.items():
        print(f"\nProcessing: {token_name}")

        # Calculate averages
        avg_raw_sentiment = sum(p.get('raw_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_aggregate_sentiment = sum(p.get('aggregate_sentiment_score', 0.0) for p in posts) / len(posts)
        avg_engagement = sum(p.get('engagement_score', 0.0) for p in posts) / len(posts)

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

        # Fetch token metadata from Moralis API
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
            chain_id = token_metadata.get('chain', '0x1')
            print(f"  ✓ Found: {token_metadata.get('name')} at ${token_price:.8f}")
            if token_logo:
                print(f"  ✓ Logo: {token_logo[:60]}...")
        else:
            print(f"  ✗ Not found in Moralis - using defaults")

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

    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coin_data, f, indent=2, ensure_ascii=False)

    print(f"\n=== Conversion Complete ===")
    print(f"Total unique coins: {len(coin_data)}")
    print(f"Total posts processed: {len(sentiment_data)}")
    print(f"Posts combined: {len(sentiment_data) - len(coin_data)}")

    # Count tokens found vs not found
    found_count = sum(1 for c in coin_data if c['address'] != 'N/A')
    print(f"Tokens found on-chain: {found_count}/{len(coin_data)}")

    print(f"\nTop 5 coins by sentiment:")
    for i, coin in enumerate(coin_data[:5], 1):
        address_display = coin['address'][:10] + '...' if coin['address'] != 'N/A' else 'N/A'
        price_display = f"${coin['price']:.8f}" if coin['price'] < 1 else f"${coin['price']:.2f}"
        print(f"{i}. {coin['name']}: Sentiment {coin['aggregate_sentiment_score']} | "
              f"Confidence: {coin['confidence']}% | {coin['recommendation']} | "
              f"Price: {price_display} | Address: {address_display}")
        if coin.get('logo'):
            print(f"   Logo: ✓")

    # Show recommendation breakdown
    buy_count = sum(1 for c in coin_data if c['recommendation'] == 'BUY')
    hold_count = sum(1 for c in coin_data if c['recommendation'] == 'HOLD')
    sell_count = sum(1 for c in coin_data if c['recommendation'] == 'SELL')
    print(f"\nRecommendations: {buy_count} BUY | {hold_count} HOLD | {sell_count} SELL")
    print(f"\nOutput saved to: {output_path}")

if __name__ == "__main__":
    convert_sentiment_to_coin_data("sentiment.json", "coin-data.json")
