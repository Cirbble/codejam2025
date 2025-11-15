"""Jupiter API client for Solana token trading."""
import os
import requests
import base64
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import Transaction, VersionedTransaction
import base58

load_dotenv()

# Try to use requests with custom DNS resolver if available
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

# Jupiter API endpoints (updated October 2025)
# quote-api.jup.ag was deprecated - new endpoints are lite-api.jup.ag (free) or api.jup.ag (pro)
JUPITER_QUOTE_URL = "https://lite-api.jup.ag/swap/v1/quote"
JUPITER_SWAP_URL = "https://lite-api.jup.ag/swap/v1/swap"
JUPITER_TOKENS_URL = "https://token.jup.ag/all"

# Solana mint addresses
SOL_MINT = "So11111111111111111111111111111111111111112"  # SOL

__all__ = ["JupiterClient", "SOL_MINT"]


class JupiterClient:
    """Client for Jupiter Aggregator API - Solana DEX aggregator."""
    
    def __init__(self):
        """Initialize Jupiter client with wallet."""
        # Load private key from .env
        private_key_str = os.getenv("SOLANA_PRIVATE_KEY")
        if not private_key_str:
            raise ValueError("SOLANA_PRIVATE_KEY not found in .env file")
        
        # Create keypair from private key (64-byte format: 32-byte seed + 32-byte public key)
        private_key_bytes = base58.b58decode(private_key_str)
        if len(private_key_bytes) != 64:
            raise ValueError(f"Invalid private key length: {len(private_key_bytes)} bytes. Expected 64 bytes.")
        self.keypair = Keypair.from_bytes(private_key_bytes)
        self.wallet_address = str(self.keypair.pubkey())
        
        # Connect to Solana RPC (try multiple endpoints for reliability)
        rpc_endpoints = [
            "https://api.mainnet-beta.solana.com",
            "https://solana-api.projectserum.com",
            "https://rpc.ankr.com/solana"
        ]
        self.solana_client = None
        for endpoint in rpc_endpoints:
            try:
                test_client = Client(endpoint)
                # Quick test
                test_client.get_slot()
                self.solana_client = test_client
                break
            except:
                continue
        
        if not self.solana_client:
            self.solana_client = Client("https://api.mainnet-beta.solana.com")  # Fallback
        
        print(f"🔑 Jupiter client initialized for wallet: {self.wallet_address[:8]}...{self.wallet_address[-8:]}")
    
    def get_token_address_from_ticker(self, ticker: str) -> Optional[str]:
        """Get Solana token mint address from ticker symbol.
        
        Args:
            ticker: Token ticker symbol (e.g., "BONK", "KENDU")
            
        Returns:
            Token mint address or None if not found
        """
        ticker_upper = ticker.upper()
        
        # Method 1: Try Jupiter token list
        try:
            response = requests.get(JUPITER_TOKENS_URL, timeout=10)
            response.raise_for_status()
            tokens = response.json()
            
            for token in tokens:
                if token.get("symbol", "").upper() == ticker_upper:
                    address = token.get("address")
                    print(f"✅ Found token {ticker} via Jupiter: {address}")
                    return address
        except Exception as e:
            print(f"⚠️ Jupiter token list unavailable: {e}")
        
        # Method 2: Try Birdeye API (fallback)
        try:
            birdeye_url = "https://public-api.birdeye.so/defi/tokenlist"
            params = {"sort_by": "v24hUSD", "sort_type": "desc", "offset": 0, "limit": 100}
            response = requests.get(birdeye_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            tokens = data.get("data", {}).get("tokens", [])
            
            for token in tokens:
                if token.get("symbol", "").upper() == ticker_upper:
                    address = token.get("address")
                    print(f"✅ Found token {ticker} via Birdeye: {address}")
                    return address
        except Exception as e:
            print(f"⚠️ Birdeye API unavailable: {e}")
        
        print(f"❌ Token {ticker} not found in any token list")
        return None
    
    def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50, retries: int = 3) -> Optional[Dict[str, Any]]:
        """Get swap quote from Jupiter with retry logic.
        
        Args:
            input_mint: Input token mint address (e.g., SOL_MINT)
            output_mint: Output token mint address
            amount: Amount in smallest unit (lamports for SOL, or token's smallest unit)
            slippage_bps: Slippage in basis points (50 = 0.5%)
            retries: Number of retry attempts
            
        Returns:
            Quote dictionary or None if failed
        """
        import time
        
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": slippage_bps
        }
        
        for attempt in range(retries):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 10)  # Exponential backoff
                    print(f"   ⏳ Retrying quote (attempt {attempt + 1}/{retries}) after {delay}s...")
                    time.sleep(delay)
                
                response = requests.get(JUPITER_QUOTE_URL, params=params, timeout=15)
                response.raise_for_status()
                quote = response.json()
                
                if "error" in quote:
                    print(f"❌ Quote error: {quote['error']}")
                    return None
                
                return quote
                
            except requests.exceptions.RequestException as e:
                if attempt < retries - 1:
                    continue  # Retry
                else:
                    print(f"❌ Error getting quote after {retries} attempts: {e}")
                    return None
            except Exception as e:
                print(f"❌ Unexpected error getting quote: {e}")
                return None
        
        return None
    
    def execute_swap(self, quote: Dict[str, Any], wrap_sol: bool = True) -> Optional[str]:
        """Execute swap using Jupiter API.
        
        Args:
            quote: Quote dictionary from get_quote()
            wrap_sol: Whether to wrap/unwrap SOL automatically
            
        Returns:
            Transaction signature (tx hash) or None if failed
        """
        try:
            swap_payload = {
                "quoteResponse": quote,
                "userPublicKey": self.wallet_address,
                "wrapAndUnwrapSol": wrap_sol,
                "dynamicComputeUnitLimit": True,
                "prioritizationFeeLamports": "auto"
            }
            
            response = requests.post(JUPITER_SWAP_URL, json=swap_payload, timeout=30)
            response.raise_for_status()
            swap_data = response.json()
            
            if "error" in swap_data:
                print(f"❌ Swap error: {swap_data['error']}")
                return None
            
            swap_transaction = swap_data.get("swapTransaction")
            if not swap_transaction:
                print(f"❌ No swap transaction in response: {swap_data}")
                return None
            
            # Deserialize and sign transaction (v1 API returns versioned transactions)
            transaction_bytes = base64.b64decode(swap_transaction)
            try:
                # Jupiter v1 uses versioned transactions (v0)
                from solders.message import to_bytes_versioned
                from solders.signature import Signature
                
                transaction = VersionedTransaction.from_bytes(transaction_bytes)
                
                # Sign the message
                message_bytes = to_bytes_versioned(transaction.message)
                signature = self.keypair.sign_message(message_bytes)
                
                # Create signed transaction
                signed_tx = VersionedTransaction.populate(
                    transaction.message,
                    [signature]
                )
            except Exception as e:
                print(f"⚠️ Could not use VersionedTransaction: {e}")
                # Fallback to legacy Transaction
                transaction = Transaction.from_bytes(transaction_bytes)
                transaction.sign(self.keypair)
                signed_tx = transaction
            
            # Send transaction
            result = self.solana_client.send_transaction(signed_tx)
            tx_signature = str(result.value)
            
            print(f"✅ Swap transaction sent: {tx_signature}")
            return tx_signature
            
        except Exception as e:
            print(f"❌ Error executing swap: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def buy_token(self, ticker_or_address: str, sol_amount: float, slippage_bps: int = 50) -> Optional[str]:
        """Buy a token using SOL.
        
        Args:
            ticker_or_address: Token ticker symbol (e.g., "BONK") or mint address
            sol_amount: Amount of SOL to spend
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)
            
        Returns:
            Transaction signature or None if failed
        """
        print(f"\n🛒 Buying {ticker_or_address[:12]}...{ticker_or_address[-4:] if len(ticker_or_address) > 20 else ticker_or_address} with {sol_amount} SOL...")
        
        # Check if it's already an address (43-44 chars for Solana addresses)
        if len(ticker_or_address) >= 32 and len(ticker_or_address) <= 44:
            token_address = ticker_or_address
            print(f"   ✅ Using provided token address")
        else:
            # Get token address from ticker
            token_address = self.get_token_address_from_ticker(ticker_or_address)
            if not token_address:
                return None
        
        # Convert SOL to lamports
        amount_lamports = int(sol_amount * 1e9)
        
        # Get quote
        print(f"📊 Getting quote...")
        quote = self.get_quote(SOL_MINT, token_address, amount_lamports, slippage_bps)
        if not quote:
            return None
        
        # Show quote details
        out_amount = quote.get("outAmount", "0")
        print(f"💰 Expected output: {int(out_amount) / 1e6:.2f} tokens (approx)")
        
        # Execute swap
        print(f"⚡ Executing swap...")
        tx_signature = self.execute_swap(quote)
        
        return tx_signature
    
    def sell_token(self, ticker: str, token_amount: float, token_decimals: int = 6, slippage_bps: int = 50) -> Optional[str]:
        """Sell a token for SOL.
        
        Args:
            ticker: Token ticker symbol
            token_amount: Amount of tokens to sell
            token_decimals: Token decimals (usually 6-9 for Solana tokens)
            slippage_bps: Slippage tolerance in basis points
            
        Returns:
            Transaction signature or None if failed
        """
        print(f"\n💸 Selling {token_amount} {ticker} for SOL...")
        
        # Get token address
        token_address = self.get_token_address_from_ticker(ticker)
        if not token_address:
            return None
        
        # Convert token amount to smallest unit
        amount_tokens = int(token_amount * (10 ** token_decimals))
        
        # Get quote
        print(f"📊 Getting quote...")
        quote = self.get_quote(token_address, SOL_MINT, amount_tokens, slippage_bps)
        if not quote:
            return None
        
        # Show quote details
        out_amount = quote.get("outAmount", "0")
        print(f"💰 Expected output: {int(out_amount) / 1e9:.4f} SOL")
        
        # Execute swap
        print(f"⚡ Executing swap...")
        tx_signature = self.execute_swap(quote)
        
        return tx_signature
    
    def get_balance(self) -> float:
        """Get SOL balance of wallet.
        
        Returns:
            Balance in SOL
        """
        try:
            balance_response = self.solana_client.get_balance(self.keypair.pubkey())
            balance_lamports = balance_response.value
            return balance_lamports / 1e9
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return 0.0

