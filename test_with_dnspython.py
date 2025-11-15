"""Test Jupiter API with custom DNS resolution."""
import requests
import dns.resolver

try:
    # Resolve using Google DNS
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']
    
    answers = resolver.resolve('quote-api.jup.ag', 'A')
    ip = str(answers[0])
    print(f"✅ Resolved quote-api.jup.ag to {ip}")
    
    # Try connecting with IP and Host header
    url = f"https://{ip}/v6/quote"
    headers = {"Host": "quote-api.jup.ag"}
    
    params = {
        "inputMint": "So11111111111111111111111111111111111111112",
        "outputMint": "So11111111111111111111111111111111111111112",
        "amount": "1000000",
        "slippageBps": "50"
    }
    
    print(f"Testing connection to {ip}...")
    response = requests.get(url, params=params, headers=headers, timeout=10, verify=True)
    print(f"✅ Success! Status: {response.status_code}")
    print(f"Response preview: {response.text[:200]}")
    
except ImportError:
    print("❌ dnspython not installed. Install with: pip install dnspython")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

