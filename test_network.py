"""Test network connectivity to Jupiter API."""
import requests
import socket

def test_dns_resolution(hostname):
    """Test if DNS can resolve a hostname."""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ {hostname} resolves to {ip}")
        return True
    except socket.gaierror as e:
        print(f"❌ {hostname} DNS resolution failed: {e}")
        return False

def test_http_connection(url):
    """Test HTTP connection to a URL."""
    try:
        response = requests.get(url, timeout=5)
        print(f"✅ {url} - Status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ {url} - Error: {e}")
        return False

print("=" * 60)
print("Network Connectivity Test")
print("=" * 60)

print("\n1️⃣ Testing DNS Resolution...")
jupiter_domains = [
    "quote-api.jup.ag",
    "token.jup.ag",
    "api.mainnet-beta.solana.com"
]

dns_ok = True
for domain in jupiter_domains:
    if not test_dns_resolution(domain):
        dns_ok = False

print("\n2️⃣ Testing HTTP Connections...")
test_urls = [
    "https://quote-api.jup.ag/v6/quote?inputMint=So11111111111111111111111111111111111111112&outputMint=So11111111111111111111111111111111111111112&amount=1000000",
    "https://api.mainnet-beta.solana.com",
]

http_ok = True
for url in test_urls:
    if not test_http_connection(url):
        http_ok = False

print("\n" + "=" * 60)
if dns_ok and http_ok:
    print("✅ Network connectivity looks good!")
else:
    print("❌ Network issues detected")
    print("\n💡 Solutions:")
    print("   1. Check your internet connection")
    print("   2. Try flushing DNS: ipconfig /flushdns (Windows)")
    print("   3. Try different DNS server (8.8.8.8 or 1.1.1.1)")
    print("   4. Check firewall/VPN settings")
    print("   5. Wait a few minutes and try again")
print("=" * 60)

