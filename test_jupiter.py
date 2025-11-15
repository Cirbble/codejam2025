"""Test Jupiter API connection and token lookup."""
from src.jupiter_client import JupiterClient

def test_jupiter():
    """Test Jupiter API functionality."""
    print("=" * 60)
    print("Testing Jupiter API")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n1️⃣ Initializing Jupiter client...")
        client = JupiterClient()
        
        # Test token lookup
        print("\n2️⃣ Testing token lookup...")
        test_tickers = ["BONK", "SOL", "USDC"]
        
        for ticker in test_tickers:
            address = client.get_token_address_from_ticker(ticker)
            if address:
                print(f"   ✅ {ticker}: {address}")
            else:
                print(f"   ❌ {ticker}: Not found")
        
        # Test quote (without executing)
        print("\n3️⃣ Testing quote API...")
        bonk_address = client.get_token_address_from_ticker("BONK")
        if bonk_address:
            # Get quote for 0.01 SOL -> BONK (small test amount)
            quote = client.get_quote(
                input_mint=client.SOL_MINT,
                output_mint=bonk_address,
                amount=10_000_000,  # 0.01 SOL in lamports
                slippage_bps=50  # 0.5% slippage
            )
            
            if quote:
                print("   ✅ Quote received successfully!")
                in_amount = quote.get("inAmount", "0")
                out_amount = quote.get("outAmount", "0")
                print(f"   📊 Input: {int(in_amount) / 1e9:.4f} SOL")
                print(f"   📊 Output: {int(out_amount) / 1e6:.2f} BONK (approx)")
            else:
                print("   ⚠️ Quote failed (might be liquidity issue)")
        
        # Check balance
        print("\n4️⃣ Checking wallet balance...")
        balance = client.get_balance()
        print(f"   💰 Balance: {balance:.4f} SOL")
        
        if balance < 0.01:
            print("   ⚠️ Low balance - fund your wallet to enable trading")
        else:
            print("   ✅ Sufficient balance for trading!")
        
        print("\n" + "=" * 60)
        print("✅ Jupiter API test complete!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_jupiter()
    exit(0 if success else 1)

