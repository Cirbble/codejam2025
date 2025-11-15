# Coin'ed - Quick Start Guide

## What You Have

A fully functional cryptocurrency sentiment analysis dashboard with:

✅ **Dashboard UI** - Dark themed crypto dashboard matching your design
✅ **Coin Cards** - Display individual cryptocurrencies with price, change %, and mini charts
✅ **Portfolio View** - Yellow sidebar showing your coin distribution
✅ **Interactive Chart** - Large chart with timeframe selection and coin switching
✅ **Control Panel** - Toggle switches for Scraper, Buyer, and Seller agents
✅ **JSON Parser** - Ready to receive and parse scraped data
✅ **Dynamic Tabs** - Automatically creates new tabs for new coins

## Quick Start

### 1. Run the Application

```bash
cd coin-ed
npm install  # If not already done
npm start
```

Open your browser to: **http://localhost:4200**

### 2. See It In Action

Click the **"📊 Load Example Scraped Data"** button to see how scraped data updates the dashboard.

### 3. Toggle the Agents

Use the three toggle switches at the top to enable/disable:
- 🌐 Web Scraper
- 💰 AI Buyer Agent  
- 💸 AI Seller Agent

(These currently log to console - ready for backend integration)

## File Structure

```
coin-ed/
├── src/app/
│   ├── components/
│   │   ├── dashboard/           ← Main container
│   │   ├── coin-card/           ← Individual coin displays
│   │   ├── portfolio/           ← Portfolio sidebar
│   │   ├── chart/               ← Price chart with Chart.js
│   │   └── control-panel/       ← Agent toggles
│   ├── services/
│   │   ├── data.service.ts      ← Core data management
│   │   └── data-loader.service.ts ← Load JSON files
│   └── models/
│       └── coin.model.ts        ← TypeScript interfaces
├── public/
│   └── example-data.json        ← Sample scraped data
├── PROJECT_README.md            ← Detailed documentation
└── INTEGRATION_GUIDE.md         ← Backend integration instructions
```

## Features Explained

### 🎯 Dynamic Coin Tabs
When you send JSON data with a new `coinId`, it automatically creates a new coin card. If the `coinId` exists, it updates that coin's data.

### 📊 Sentiment Tracking
Each coin can have sentiment data from multiple sources (Reddit, Twitter, etc.) with individual sentiment scores.

### 💹 Real-time Updates
The UI uses Angular signals for reactive updates - change the data and the UI instantly reflects it.

### 🎨 Visual Feedback
- Green = Positive change
- Red = Negative change  
- Gold = Selected/Active

## Next Steps for Your Project

### Backend Integration

1. **Build Your Web Scraper**
   - Scrape Reddit (r/cryptocurrency, r/bitcoin, etc.)
   - Scrape Twitter/X for coin mentions
   - Parse sentiment from text
   - Format as JSON (see INTEGRATION_GUIDE.md)

2. **Connect the Scraper**
   - Send JSON data to the DataService
   - Use WebSocket for real-time updates
   - Or use HTTP polling

3. **Build AI Agents**
   - Buyer Agent: Analyzes sentiment, decides to buy
   - Seller Agent: Monitors portfolio, decides to sell
   - Connect to the toggle switches

4. **Add Trading Logic**
   - Connect to a crypto exchange API
   - Execute buy/sell orders
   - Update portfolio balances

### Example: Adding a New Coin from Scraper

Your scraper finds "PEPE" coin trending on Reddit:

```javascript
const newCoin = {
  coinId: "pepe",
  name: "Pepe",
  symbol: "PEPE",
  price: 0.000001,
  balance: 10000000,
  changePercentage: 0.35,
  feedback: "Viral on Reddit",
  sentiment: {
    type: "positive",
    score: 0.92,
    sources: [
      {
        platform: "reddit",
        url: "https://reddit.com/r/cryptocurrency/...",
        text: "PEPE going to the moon! 🚀",
        sentiment: 0.95
      }
    ]
  }
};

// Send to frontend
dataService.parseScrapedData(newCoin);
```

**Result**: A new PEPE coin card appears on the dashboard automatically!

## Mock Data

The app starts with 4 mock coins:
- Bitcoin (BTC)
- Litecoin (LTC)
- Ethereum (ETH)
- Solana (SOL)

Click "Load Example Scraped Data" to add:
- Dogecoin (DOGE)
- Shiba Inu (SHIB)

## Technologies Used

- **Angular 20** (latest, with signals)
- **TypeScript** 
- **Chart.js** (charts)
- **CSS3** (styling)
- **Zoneless** (performance)

## Common Commands

```bash
# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test

# Generate new component
ng generate component components/my-component
```

## Customization

### Colors
Edit `src/app/components/dashboard/dashboard.component.css`:
- Background: `#0a0a0a` to `#1a1a1a`
- Accent: `#FFD700` (gold)
- Positive: `#00d4aa` (teal)
- Negative: `#ff6b6b` (red)

### Add More Coins
Add to mock data in `data.service.ts` → `initializeMockData()`

### Modify Chart
Edit `src/app/components/chart/chart.component.ts` for Chart.js options

## Troubleshooting

**Server won't start?**
```bash
rm -rf node_modules package-lock.json
npm install
npm start
```

**Data not loading?**
- Check browser console (F12)
- Verify example-data.json is in /public folder
- Check network tab for 404 errors

**Toggles not working?**
- Check console for click events
- Verify control-panel component is loaded

## Resources

- 📖 [PROJECT_README.md](./PROJECT_README.md) - Full documentation
- 🔌 [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - Backend integration
- 🌐 [Angular Docs](https://angular.dev)
- 📊 [Chart.js Docs](https://www.chartjs.org)

## Demo Video Flow

1. **Show the dashboard** with default coins
2. **Click toggles** to show agent controls
3. **Click "Load Example Data"** to demonstrate scraper simulation
4. **Watch new coins appear** (Dogecoin, Shiba)
5. **Show portfolio update** with new percentages
6. **Switch coins** in the chart dropdown
7. **Explain** how backend will send real data

---

**You're all set! 🚀**

The frontend is complete and ready to receive data from your web scrapers and AI agents. Focus on building the backend integration next!

For CodeJam 2025 presentation:
1. Show the UI (it matches your design!)
2. Demo the data loading
3. Explain the architecture
4. Show the integration guide
5. Walk through sentiment analysis concept

Good luck! 🎉

