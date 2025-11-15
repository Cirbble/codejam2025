"""Test direct connection to Jupiter API using IP if possible."""
import requests
import socket

# Try to get IP address
try:
    ip = socket.gethostbyname("quote-api.jup.ag")
    print(f"✅ Resolved quote-api.jup.ag to {ip}")
    
    # Try connecting directly
    url = f"https://{ip}/v6/quote"
    headers = {"Host": "quote-api.jup.ag"}  # SNI header
    
    params = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "outputMint": "So11111111111111111111111111111111111111112",
        "amount": "1000000",
        "slippageBps": "50"
    }
    
    print(f"Testing direct connection...")
    response = requests.get(url, params=params, headers=headers, timeout=10, verify=True)
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
except socket.gaierror as e:
    print(f"❌ DNS resolution failed: {e}")
except Exception as e:
    print(f"❌ Error: {e}")

