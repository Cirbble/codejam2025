"""
Moralis Solana API Integration (Python)
Complete setup for interacting with Moralis Solana blockchain API

Installation:
    pip install requests python-dotenv

Setup:
    1. Create .env file in project root
    2. Add: MORALIS_API_KEY=your_key_here
    3. Get your key from: https://admin.moralis.io/
"""

import os
import requests
import time
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MORALIS_CONFIG = {
    'SOLANA_GATEWAY': 'https://solana-gateway.moralis.io',
    'DEEP_INDEX': 'https://deep-index.moralis.io/api/v2.2'
}


class MoralisSolanaAPI:
    """Complete Moralis Solana API wrapper with all endpoints"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Moralis API client

        Args:
            api_key: Moralis API key. If not provided, reads from MORALIS_API_KEY env var
        """
        self.api_key = api_key or os.getenv('MORALIS_API_KEY')
        if not self.api_key:
            raise ValueError("MORALIS_API_KEY not found. Set it in .env file or pass as parameter")

        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

    def _validate_address(self, address: str) -> bool:
        """Validate Solana address format (base58, 32-44 chars)"""
        import re
        pattern = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
        return bool(re.match(pattern, address))

    def _fetch_with_retry(self, url: str, retries: int = None) -> Optional[Dict]:
        """
        Make HTTP request with retry logic

        Args:
            url: API endpoint URL
            retries: Number of retries (default: self.max_retries)

        Returns:
            JSON response as dict or None on failure
        """
        if retries is None:
            retries = self.max_retries

        headers = {
            'Accept': 'application/json',
            'X-API-Key': self.api_key
        }

        for attempt in range(retries + 1):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    print(f"Request failed, retrying... ({retries - attempt} attempts left)")
                    time.sleep(self.retry_delay)
                else:
                    print(f"Error fetching {url}: {e}")
                    return None

        return None

    def get_token_metadata(self, address: str) -> Optional[Dict]:
        """
        Get token metadata

        Args:
            address: Solana token mint address

        Returns:
            Dict with: name, symbol, logo, decimals, supply, metadata
        """
        if not self._validate_address(address):
            print(f"Invalid Solana address: {address}")
            return None

        url = f"{MORALIS_CONFIG['SOLANA_GATEWAY']}/token/mainnet/{address}/metadata"
        data = self._fetch_with_retry(url)

        if not data:
            return None

        return {
            'address': data.get('mint', address),
            'name': data.get('name', 'Unknown'),
            'symbol': data.get('symbol', '???'),
            'logo': data.get('logoURI') or data.get('logo'),
            'decimals': data.get('decimals', 9),
            'supply': data.get('supply'),
            'metadata': data
        }

    def get_token_price(self, address: str) -> Optional[Dict]:
        """
        Get token price

        Args:
            address: Solana token mint address

        Returns:
            Dict with: priceUSD, 24h_change, liquidity, volume
        """
        if not self._validate_address(address):
            print(f"Invalid Solana address: {address}")
            return None

        url = f"{MORALIS_CONFIG['SOLANA_GATEWAY']}/token/mainnet/{address}/price"
        data = self._fetch_with_retry(url)

        if not data:
            return None

        return {
            'priceUSD': data.get('usdPrice', 0),
            '24h_change': data.get('24hrPercentChange'),
            'liquidity': data.get('liquidity', {}).get('usd'),
            'volume': data.get('volume24h')
        }

    def get_trending_tokens(self) -> List[Dict]:
        """
        Get trending tokens across all chains

        Returns:
            List of trending token dicts
        """
        url = f"{MORALIS_CONFIG['DEEP_INDEX']}/tokens/trending"
        data = self._fetch_with_retry(url)

        if not data:
            return []

        return data.get('tokens', [])

    def get_token_pairs(self, address: str) -> List[Dict]:
        """
        Get token trading pairs

        Args:
            address: Solana token mint address

        Returns:
            List of pair dicts with: pairAddress, baseToken, quoteToken, liquidity, volume
        """
        if not self._validate_address(address):
            print(f"Invalid Solana address: {address}")
            return []

        url = f"{MORALIS_CONFIG['SOLANA_GATEWAY']}/token/mainnet/{address}/pairs"
        data = self._fetch_with_retry(url)

        if not data or 'pairs' not in data:
            return []

        return [
            {
                'pairAddress': pair.get('pairAddress'),
                'baseToken': pair.get('baseToken'),
                'quoteToken': pair.get('quoteToken'),
                'liquidity': pair.get('liquidity', {}).get('usd', 0),
                'volume24h': pair.get('volume24h', 0)
            }
            for pair in data['pairs']
        ]

    def get_pair_stats(self, pair_address: str) -> Optional[Dict]:
        """
        Get trading pair statistics

        Args:
            pair_address: Solana pair address

        Returns:
            Dict with: pairAddress, priceUSD, liquidity, volume24h, priceChange24h
        """
        if not self._validate_address(pair_address):
            print(f"Invalid Solana pair address: {pair_address}")
            return None

        url = f"{MORALIS_CONFIG['SOLANA_GATEWAY']}/token/mainnet/pairs/{pair_address}/stats"
        data = self._fetch_with_retry(url)

        if not data:
            return None

        return {
            'pairAddress': pair_address,
            'priceUSD': data.get('priceUsd', 0),
            'liquidity': data.get('liquidity', {}).get('usd', 0),
            'volume24h': data.get('volume24h', 0),
            'priceChange24h': data.get('priceChange24h', 0)
        }

    def get_token_holders(self, address: str) -> List[Dict]:
        """
        Get token holders

        Args:
            address: Solana token mint address

        Returns:
            List of holder dicts with: address, balance, percentage
        """
        if not self._validate_address(address):
            print(f"Invalid Solana address: {address}")
            return []

        url = f"{MORALIS_CONFIG['SOLANA_GATEWAY']}/token/mainnet/holders/{address}"
        data = self._fetch_with_retry(url)

        if not data or 'holders' not in data:
            return []

        return [
            {
                'address': holder.get('address'),
                'balance': holder.get('balance'),
                'percentage': holder.get('percentage', 0)
            }
            for holder in data['holders']
        ]

    def get_full_token_data(self, address: str) -> Optional[Dict]:
        """
        MASTER FUNCTION: Get complete token data
        Combines all API calls into a single comprehensive object

        Args:
            address: Solana token mint address

        Returns:
            Dict with all token data:
                - name, symbol, logo_url
                - price, 24h_change, liquidity, volume
                - supply, holders, pairs, metadata
        """
        if not self._validate_address(address):
            print(f"Invalid Solana address: {address}")
            return None

        print(f"Fetching full token data for: {address}")

        # Fetch all data
        metadata = self.get_token_metadata(address)
        if not metadata:
            print("Failed to fetch token metadata")
            return None

        price = self.get_token_price(address)
        pairs = self.get_token_pairs(address)
        holders = self.get_token_holders(address)

        return {
            'name': metadata['name'],
            'symbol': metadata['symbol'],
            'logo_url': metadata['logo'],
            'price': price['priceUSD'] if price else 0,
            '24h_change': price['24h_change'] if price else None,
            'liquidity': price['liquidity'] if price else None,
            'volume': price['volume'] if price else None,
            'supply': metadata['supply'],
            'holders': holders,
            'pairs': pairs,
            'metadata': metadata['metadata'],
            'address': address,
            'decimals': metadata['decimals']
        }

    def get_multiple_tokens_data(self, addresses: List[str]) -> List[Dict]:
        """
        Batch fetch multiple tokens

        Args:
            addresses: List of Solana token addresses

        Returns:
            List of full token data dicts
        """
        valid_addresses = [addr for addr in addresses if self._validate_address(addr)]

        if not valid_addresses:
            print("No valid addresses provided")
            return []

        results = []
        for addr in valid_addresses:
            data = self.get_full_token_data(addr)
            if data:
                results.append(data)

        return results


# Example usage
if __name__ == "__main__":
    # Initialize API client (reads MORALIS_API_KEY from .env)
    try:
        api = MoralisSolanaAPI()

        # Example 1: Get full token data for SOL
        print("\n" + "="*60)
        print("Example 1: Get Full Token Data for SOL")
        print("="*60)

        sol_address = "So11111111111111111111111111111111111111112"
        sol_data = api.get_full_token_data(sol_address)

        if sol_data:
            print(f"\nToken: {sol_data['name']} ({sol_data['symbol']})")
            print(f"Address: {sol_data['address']}")
            print(f"Price: ${sol_data['price']:.2f}")
            print(f"24h Change: {sol_data['24h_change']:.2f}%" if sol_data['24h_change'] else "N/A")
            print(f"Decimals: {sol_data['decimals']}")
            print(f"Supply: {sol_data['supply']}")
            print(f"Logo: {sol_data['logo_url']}")
            print(f"Number of Pairs: {len(sol_data['pairs'])}")
            print(f"Number of Holders: {len(sol_data['holders'])}")

        # Example 2: Get multiple tokens
        print("\n" + "="*60)
        print("Example 2: Get Multiple Tokens")
        print("="*60)

        addresses = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"   # USDC
        ]

        tokens = api.get_multiple_tokens_data(addresses)

        for token in tokens:
            print(f"\n{token['name']} ({token['symbol']})")
            print(f"  Price: ${token['price']:.6f}")
            print(f"  Liquidity: ${token['liquidity']:,.2f}" if token['liquidity'] else "  Liquidity: N/A")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo fix this:")
        print("1. Create a .env file in your project root")
        print("2. Add: MORALIS_API_KEY=your_actual_api_key")
        print("3. Get your key from: https://admin.moralis.io/")

