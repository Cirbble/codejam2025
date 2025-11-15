# Trading Platforms for Memecoins & Automation

## Overview
This document covers the best platforms and APIs for accessing and trading memecoins, including pump.fun tokens and other Solana/Ethereum memecoins.

---

## 🎯 Best Platforms for Accessing ALL Coins

### 1. **Jupiter Aggregator** (Solana) ⭐ RECOMMENDED
- **Website**: https://jup.ag
- **API**: https://station.jup.ag/docs
- **Why**: 
  - Aggregates liquidity from ALL Solana DEXs (Raydium, Orca, Meteora, pump.fun, etc.)
  - Best prices via route optimization
  - Supports pump.fun tokens automatically
  - Free API with rate limits
- **API Features**:
  - Token search across all DEXs
  - Price quotes
  - Swap execution
  - Token metadata

### 2. **1inch Network** (Multi-chain)
- **Website**: https://1inch.io
- **API**: https://docs.1inch.io
- **Why**:
  - Supports Ethereum, BSC, Polygon, Arbitrum, Optimism, Avalanche, Base
  - Aggregates liquidity from 100+ DEXs
  - Good for Ethereum-based memecoins
- **Limitation**: Doesn't support Solana/pump.fun directly

### 3. **Birdeye** (Solana Analytics + Trading)
- **Website**: https://birdeye.so
- **API**: https://docs.birdeye.so
- **Why**:
  - Real-time Solana token data
  - Tracks pump.fun launches
  - Token discovery and analytics
  - Trading API available
- **Use Case**: Token discovery and monitoring

### 4. **DexScreener** (Multi-chain Analytics)
- **Website**: https://dexscreener.com
- **API**: https://docs.dexscreener.com
- **Why**:
  - Tracks tokens across multiple chains
  - Real-time price data
  - Token discovery
- **Limitation**: Read-only API (no trading)

---

## 🤖 Automation APIs & Libraries

### Solana Trading

#### **Jupiter API** (Best for Solana) ⭐ YES - Supports Auto Buy/Sell

**Important**: Jupiter uses **token mint addresses** (not ticker symbols directly), but you can convert ticker → address using Birdeye API or Jupiter's token search.

**Workflow for Auto Trading by Ticker Symbol:**
1. **Lookup token address** from ticker symbol (using Birdeye or Jupiter token search)
2. **Get price quote** from Jupiter
3. **Execute swap** using Jupiter API
4. **Sign and send transaction** using Solana Web3

```python
import requests
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import Transaction
import base58

# STEP 1: Convert ticker symbol to token address (using Birdeye API)
def get_token_address_from_ticker(ticker: str) -> str:
    """Get Solana token mint address from ticker symbol."""
    birdeye_url = "https://public-api.birdeye.so/defi/tokenlist"
    params = {"sort_by": "v24hUSD", "sort_type": "desc"}
    response = requests.get(birdeye_url, params=params, headers={
        "X-API-KEY": "YOUR_BIRDEYE_API_KEY"  # Free tier available
    })
    
    tokens = response.json().get("data", {}).get("tokens", [])
    for token in tokens:
        if token.get("symbol", "").upper() == ticker.upper():
            return token.get("address")
    
    # Fallback: Search Jupiter token list
    jupiter_tokens_url = "https://token.jup.ag/all"
    jupiter_tokens = requests.get(jupiter_tokens_url).json()
    for token in jupiter_tokens:
        if token.get("symbol", "").upper() == ticker.upper():
            return token.get("address")
    
    return None

# STEP 2: Get quote from Jupiter
def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50):
    """Get swap quote from Jupiter."""
    quote_url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,
        "slippageBps": slippage_bps
    }
    response = requests.get(quote_url, params=params)
    return response.json()

# STEP 3: Execute swap (auto buy/sell)
def execute_jupiter_swap(quote: dict, wallet_address: str, private_key: str):
    """Execute swap using Jupiter API."""
    swap_url = "https://quote-api.jup.ag/v6/swap"
    swap_response = requests.post(swap_url, json={
        "quoteResponse": quote,
        "userPublicKey": wallet_address,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
        "prioritizationFeeLamports": "auto"
    })
    
    swap_data = swap_response.json()
    swap_transaction = swap_data.get("swapTransaction")
    
    if not swap_transaction:
        raise Exception(f"Swap failed: {swap_data}")
    
    # STEP 4: Sign and send transaction
    client = Client("https://api.mainnet-beta.solana.com")
    keypair = Keypair.from_bytes(base58.b58decode(private_key))
    
    # Deserialize and sign transaction
    transaction_bytes = base64.b64decode(swap_transaction)
    transaction = Transaction.deserialize(transaction_bytes)
    transaction.sign(keypair)
    
    # Send transaction
    result = client.send_transaction(transaction)
    return result

# EXAMPLE: Auto buy token by ticker symbol
def auto_buy_token(ticker: str, sol_amount: float, wallet_private_key: str):
    """Automatically buy a token by ticker symbol."""
    # Convert ticker to address
    token_address = get_token_address_from_ticker(ticker)
    if not token_address:
        raise Exception(f"Token {ticker} not found")
    
    # Get quote (buying token with SOL)
    sol_mint = "So11111111111111111111111111111111111111112"  # SOL mint address
    amount_sol = int(sol_amount * 1e9)  # Convert to lamports
    
    quote = get_jupiter_quote(sol_mint, token_address, amount_sol)
    
    # Get wallet address from private key
    keypair = Keypair.from_bytes(base58.b58decode(wallet_private_key))
    wallet_address = str(keypair.pubkey())
    
    # Execute swap
    result = execute_jupiter_swap(quote, wallet_address, wallet_private_key)
    return result

# EXAMPLE: Auto sell token by ticker symbol
def auto_sell_token(ticker: str, token_amount: float, wallet_private_key: str):
    """Automatically sell a token by ticker symbol."""
    # Convert ticker to address
    token_address = get_token_address_from_ticker(ticker)
    if not token_address:
        raise Exception(f"Token {ticker} not found")
    
    # Get token decimals (usually 6-9 for Solana tokens)
    # You may need to fetch this from token metadata
    token_decimals = 6  # Default, should fetch from API
    amount_tokens = int(token_amount * (10 ** token_decimals))
    
    # Get quote (selling token for SOL)
    sol_mint = "So11111111111111111111111111111111111111112"
    quote = get_jupiter_quote(token_address, sol_mint, amount_tokens)
    
    # Execute swap
    keypair = Keypair.from_bytes(base58.b58decode(wallet_private_key))
    wallet_address = str(keypair.pubkey())
    result = execute_jupiter_swap(quote, wallet_address, wallet_private_key)
    return result
```

**Key Points:**
- ✅ **Yes, Jupiter supports auto buy/sell**
- ✅ Works with **ticker symbols** (via Birdeye/Jupiter token lookup)
- ✅ Supports **all Solana tokens** including pump.fun tokens
- ✅ **Best prices** via aggregation
- ⚠️ Requires **wallet private key** for signing transactions
- ⚠️ Need to handle **transaction signing** and **error handling**

#### **Solana Web3.py** (Direct DEX Interaction)
```python
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
import base58

# Connect to Solana
client = Client("https://api.mainnet-beta.solana.com")

# Load wallet
private_key = base58.b58decode("YOUR_PRIVATE_KEY")
keypair = Keypair.from_bytes(private_key)

# Interact with Raydium/Orca/pump.fun directly
# (Requires understanding of each DEX's program)
```

#### **Raydium SDK**
- **GitHub**: https://github.com/raydium-io/raydium-sdk
- **Use Case**: Direct Raydium DEX trading
- **Complexity**: High (requires deep Solana knowledge)

#### **Orca SDK**
- **GitHub**: https://github.com/orca-so/typescript-sdk
- **Use Case**: Direct Orca DEX trading
- **Note**: TypeScript/JavaScript only

### Ethereum/EVM Trading

#### **1inch API**
```python
import requests

# Get swap quote
quote_url = "https://api.1inch.io/v5.0/1/quote"
params = {
    "fromTokenAddress": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
    "toTokenAddress": "TOKEN_ADDRESS",
    "amount": "1000000000000000000",  # 1 ETH
    "slippage": 1  # 1%
}
response = requests.get(quote_url, params=params)
```

#### **Web3.py** (Ethereum)
```python
from web3 import Web3

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY"))

# Interact with Uniswap, SushiSwap, etc.
# (Requires contract ABIs and addresses)
```

---

## 🎯 Recommended Stack for Your Project

### For Solana Memecoins (pump.fun + others):

1. **Token Discovery**: Birdeye API or DexScreener API
2. **Price Data**: Jupiter API or Birdeye API
3. **Trading Execution**: Jupiter API (easiest) or direct Solana Web3.py
4. **Wallet Management**: Solana Web3.py with Keypair

### For Multi-chain Support:

1. **Solana**: Jupiter API
2. **Ethereum/BSC/Polygon**: 1inch API
3. **Token Discovery**: DexScreener API (multi-chain)

---

## 🔐 Security Considerations

1. **Never expose private keys** in code
2. **Use environment variables** for sensitive data
3. **Implement slippage protection** (1-5% max)
4. **Set maximum trade sizes** to limit losses
5. **Use testnet first** before mainnet
6. **Monitor gas fees** (Ethereum) and transaction costs (Solana)

---

## 📚 Resources

- **Jupiter Docs**: https://station.jup.ag/docs
- **Solana Cookbook**: https://solanacookbook.com
- **Solana Web3.py**: https://michaelhly.com/solana-py
- **1inch Docs**: https://docs.1inch.io
- **Birdeye Docs**: https://docs.birdeye.so

---

## 💡 Quick Start Example: Auto Buy/Sell by Ticker

```python
# Complete example: Auto buy token by ticker symbol
import requests
import base64
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.transaction import Transaction
import base58

# 1. Lookup token address from ticker
ticker = "BONK"  # Your token ticker
birdeye_url = f"https://public-api.birdeye.so/defi/token_overview"
params = {"address": "YOUR_TOKEN_ADDRESS"}  # Or search by symbol
# ... (see full example above)

# 2. Get quote and execute swap
# ... (see full implementation above)
```

**Simplified Flow:**
1. **Ticker → Address**: Use Birdeye API or Jupiter token list
2. **Get Quote**: Jupiter quote API
3. **Execute Swap**: Jupiter swap API  
4. **Sign & Send**: Solana Web3.py

---

## 🚨 Important Notes

- **pump.fun tokens** are automatically accessible via Jupiter API
- **Jupiter** is the easiest way to trade ANY Solana token
- **Test thoroughly** on devnet/testnet before mainnet
- **Start with small amounts** for testing
- **Monitor transaction status** and handle failures gracefully

