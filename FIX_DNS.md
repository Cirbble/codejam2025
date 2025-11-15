# Fix DNS Issue - Quick Guide

## Problem
Your router's DNS (192.168.2.1) cannot resolve Jupiter API domains, but Google DNS (8.8.8.8) can.

## Quick Fix: Change DNS to Google DNS

### Windows 10/11:
1. **Open Network Settings:**
   - Right-click network icon in system tray
   - Click "Open Network & Internet settings"
   - Click "Change adapter options"

2. **Change DNS:**
   - Right-click your active network adapter (Wi-Fi or Ethernet)
   - Click "Properties"
   - Select "Internet Protocol Version 4 (TCP/IPv4)"
   - Click "Properties"
   - Select "Use the following DNS server addresses"
   - Enter:
     - **Preferred DNS:** 8.8.8.8
     - **Alternate DNS:** 8.8.4.4
   - Click OK

3. **Restart:**
   - Restart your computer OR
   - Run: `ipconfig /flushdns` and restart terminal

### Alternative: Change DNS via Command Line (Admin)
```powershell
# Run PowerShell as Administrator, then:
netsh interface ip set dns "Wi-Fi" static 8.8.8.8
netsh interface ip add dns "Wi-Fi" 8.8.4.4 index=2
ipconfig /flushdns
```

## Test After Fix
```powershell
nslookup quote-api.jup.ag
python test_buy_hege.py
```

## Why This Happens
- Your router's DNS server may be blocking/not resolving certain domains
- Google DNS (8.8.8.8) is more reliable and faster
- This is a common issue with home routers

## After Fixing DNS
Once DNS is fixed, the buy test should work! The code is ready, just needs network connectivity.

