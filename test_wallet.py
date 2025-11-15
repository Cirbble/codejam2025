"""Test script to verify Solana wallet connection."""
import os
from dotenv import load_dotenv

def test_wallet_connection():
    """Test that we can connect to and read from the Solana wallet."""
    load_dotenv()
    
    try:
        from solders.keypair import Keypair
        from solders.pubkey import Pubkey
        from solana.rpc.api import Client
        import base58
    except ImportError:
        print("❌ Missing required libraries.")
        print("Run: pip install solana solders")
        return False
    
    # Get private key from .env
    private_key_str = os.getenv("SOLANA_PRIVATE_KEY")
    if not private_key_str:
        print("❌ SOLANA_PRIVATE_KEY not found in .env file")
        return False
    
    try:
        print("🔧 Testing Solana wallet connection...")
        print("=" * 60)
        
        # Decode private key from base58 (should be 64 bytes: 32-byte seed + 32-byte public key)
        private_key_bytes = base58.b58decode(private_key_str)
        if len(private_key_bytes) != 64:
            raise ValueError(f"Invalid private key length: {len(private_key_bytes)} bytes. Expected 64 bytes.")
        
        # Create keypair from private key
        keypair = Keypair.from_bytes(private_key_bytes)
        
        # Get public address
        public_key = keypair.pubkey()
        wallet_address = str(public_key)
        
        print(f"✅ Wallet loaded successfully!")
        print(f"📍 Wallet Address: {wallet_address}")
        
        # Connect to Solana RPC
        print("\n🌐 Connecting to Solana network...")
        client = Client("https://api.mainnet-beta.solana.com")
        
        # Get balance
        print("💰 Checking wallet balance...")
        balance_response = client.get_balance(public_key)
        balance_lamports = balance_response.value
        balance_sol = balance_lamports / 1e9
        
        print(f"✅ Balance: {balance_sol:.4f} SOL ({balance_lamports} lamports)")
        
        if balance_sol < 0.01:
            print("⚠️  Warning: Low balance. You'll need SOL for trading and transaction fees.")
        else:
            print("✅ Sufficient balance for trading!")
        
        print("\n" + "=" * 60)
        print("✅ Wallet connection test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_wallet_connection()
    exit(0 if success else 1)

