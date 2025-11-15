# Solutions for Jupiter API DNS Issues

## Problem
Jupiter API domains (`quote-api.jup.ag`, `token.jup.ag`) are not resolving via DNS.

## Solutions

### Solution 1: Flush DNS Cache (Windows)
```powershell
ipconfig /flushdns
```
Then restart your terminal and try again.

### Solution 2: Change DNS Server
1. Open Network Settings
2. Change DNS to:
   - **Google DNS**: 8.8.8.8 and 8.8.4.4
   - **Cloudflare DNS**: 1.1.1.1 and 1.0.0.1
3. Restart your computer/network adapter
4. Try again

### Solution 3: Use VPN/Proxy
If your ISP is blocking, try:
- Use a VPN
- Use a proxy
- Try mobile hotspot

### Solution 4: Check Firewall/Antivirus
- Temporarily disable firewall/antivirus
- Add exceptions for Python
- Check if corporate firewall is blocking

### Solution 5: Wait and Retry
- Could be temporary Jupiter API outage
- Wait 5-10 minutes and try again
- Check Jupiter status: https://status.jupiter.ag

### Solution 6: Use Alternative Endpoints
We can try:
- Direct IP addresses (if available)
- Alternative Jupiter endpoints
- Proxy through different server

### Solution 7: Manual Token Address
Since we already have HEGE address, we can:
- Skip token lookup
- Use token address directly
- Only need quote API to work

## Quick Fix Commands

```powershell
# Flush DNS
ipconfig /flushdns

# Test DNS resolution
nslookup quote-api.jup.ag

# Test connectivity
ping quote-api.jup.ag
```

## Current Status
- ✅ Wallet: Connected
- ✅ Token Address: Found (ULwSJmmpxmnRfpu6BjnK6rprKXqD5jXUmPpS1FxHXFy)
- ✅ Code: Ready
- ❌ Network: DNS resolution failing

## Next Steps
1. Try flushing DNS: `ipconfig /flushdns`
2. Change DNS to 8.8.8.8
3. Wait 5 minutes and retry
4. Check if VPN helps

