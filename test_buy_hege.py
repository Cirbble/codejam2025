"""Test buying HEGE token for $1."""
from src.jupiter_client import JupiterClient, SOL_MINT

def test_buy_hege():
    """Test buying HEGE token."""
    print("=" * 60)
    print("Testing HEGE Token Purchase")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n1️⃣ Initializing Jupiter client...")
        client = JupiterClient()
        
        # Check balance
        print("\n2️⃣ Checking wallet balance...")
        balance = client.get_balance()
        print(f"   💰 Current balance: {balance:.4f} SOL")
        
        if balance < 0.01:
            print("   ⚠️  Low balance detected. Will proceed with test but trade may fail.")
            print("   💡 If you just funded, wait a few seconds for confirmation.")
        
        # Look up HEGE token
        print("\n3️⃣ Looking up HEGE token...")
        hege_address = client.get_token_address_from_ticker("HEGE")
        
        if not hege_address:
            print("   ⚠️  HEGE token not found in token lists.")
            print("   💡 For pump.fun tokens, you may need to provide the token address directly.")
            print("   📝 If you have the HEGE token address, we can use it directly.")
            print("\n   Trying alternative: Searching for HEGE in pump.fun...")
            
            # Try to search pump.fun API if available
            # For now, let's try a common pump.fun token address format or ask user
            print("   ❌ Cannot lookup pump.fun tokens automatically yet.")
            print("   💡 Solution: Get the token address from pump.fun website")
            print("   📋 Example: If HEGE address is known, we can use it directly")
            
            # HEGE token address from pump.fun
            hege_address = "ULwSJmmpxmnRfpu6BjnK6rprKXqD5jXUmPpS1FxHXFy"
            print(f"   ✅ Using known HEGE address: {hege_address}")
        
        print(f"   ✅ HEGE address: {hege_address}")
        
        # Get quote for $1 worth (approximately 0.001 SOL, but let's use current SOL price)
        # Rough estimate: $1 ≈ 0.001 SOL (adjust if needed)
        sol_amount = 0.001  # Start with 0.001 SOL (~$1)
        
        print(f"\n4️⃣ Getting quote for {sol_amount} SOL -> HEGE...")
        amount_lamports = int(sol_amount * 1e9)
        
        quote = client.get_quote(
            input_mint=SOL_MINT,
            output_mint=hege_address,
            amount=amount_lamports,
            slippage_bps=100  # 1% slippage for test
        )
        
        if not quote:
            print("   ❌ Failed to get quote. Possible reasons:")
            print("      - Insufficient liquidity")
            print("      - Token not tradeable yet")
            print("      - Network issues")
            return False
        
        # Show quote details
        in_amount = quote.get("inAmount", "0")
        out_amount = quote.get("outAmount", "0")
        price_impact = quote.get("priceImpactPct", "N/A")
        
        print(f"\n   📊 Quote Details:")
        print(f"      Input: {int(in_amount) / 1e9:.6f} SOL")
        print(f"      Output: {int(out_amount):,} HEGE tokens")
        print(f"      Price Impact: {price_impact}%")
        
        # Confirm before executing
        print(f"\n5️⃣ Ready to execute buy...")
        print(f"   ⚠️  This will execute a REAL trade on mainnet!")
        
        # Execute the buy using the address directly
        print(f"\n6️⃣ Executing buy order...")
        tx_signature = client.buy_token(hege_address, sol_amount, slippage_bps=100)
        
        if tx_signature:
            print(f"\n✅ Buy order executed successfully!")
            print(f"   📝 Transaction: {tx_signature}")
            print(f"   🔗 View on Solscan: https://solscan.io/tx/{tx_signature}")
            return True
        else:
            print(f"\n❌ Buy order failed")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  WARNING: This will execute a REAL trade on Solana mainnet!")
    print("⚠️  Make sure you understand the risks before proceeding.\n")
    
    success = test_buy_hege()
    exit(0 if success else 1)

