# Coin'ed - AI-Powered Crypto Sentiment Dashboard

A cryptocurrency sentiment analysis dashboard that visualizes data scraped from social media platforms including Reddit, Twitter/X, and other sources.

## Features

### Current Implementation

- **Dashboard UI**: Modern, dark-themed cryptocurrency dashboard
- **Coin Cards**: Individual cards for each cryptocurrency showing:
  - Current price and balance
  - Percentage change (positive/negative)
  - Mini chart visualization
  - Coin icon and symbol
  
- **Portfolio View**: Yellow-themed portfolio card displaying:
  - Individual coin holdings
  - Percentage distribution
  - Total balance calculation

- **Interactive Chart**: Main chart component with:
  - Chart.js integration for smooth visualizations
  - Multiple timeframe options (1h, 3h, 1d, 1w, 1m)
  - Coin selector dropdown
  - Real-time price display

- **Control Panel**: Toggle switches for:
  - Web Scraper (on/off)
  - AI Buyer Agent (on/off)
  - AI Seller Agent (on/off)

### Architecture Ready for Integration

#### JSON Data Parsing
The `DataService` is architected to handle incoming JSON data from backend scrapers:

```typescript
// Example JSON format for scraped data
{
  "coinId": "bitcoin",
  "name": "Bitcoin",
  "symbol": "BTC",
  "price": 52291,
  "balance": 52291,
  "changePercentage": 0.25,
  "chartData": [/* array of price points */],
  "sentiment": {
    "type": "positive",
    "score": 0.85,
    "sources": [
      {
        "platform": "reddit",
        "url": "https://reddit.com/r/cryptocurrency/...",
        "text": "...",
        "sentiment": 0.9
      }
    ]
  }
}
```

#### Dynamic Tab Management
- New JSON entries automatically create new memecoin tabs
- Existing tabs update when new data arrives for the same coin
- Portfolio recalculates automatically

## Project Structure

```
src/app/
├── components/
│   ├── dashboard/          # Main dashboard container
│   ├── coin-card/          # Individual coin cards
│   ├── portfolio/          # Portfolio sidebar
│   ├── chart/              # Main price chart
│   └── control-panel/      # Agent control toggles
├── services/
│   └── data.service.ts     # Central data management & JSON parsing
└── models/
    └── coin.model.ts       # TypeScript interfaces for data structures
```

## Setup & Installation

### Prerequisites
- Node.js (v18 or higher)
- npm

### Install Dependencies
```bash
cd coin-ed
npm install
```

### Run Development Server
```bash
npm start
# or
ng serve
```

Navigate to `http://localhost:4200/`

## Integration Guide

### Connecting Backend Scrapers

To integrate your web scraping backend:

1. **Send JSON Data**: Post scraped data to the frontend using the format above
2. **The DataService will automatically**:
   - Parse the incoming JSON
   - Create new coin tabs or update existing ones
   - Update sentiment data
   - Recalculate portfolio balances

Example integration code:
```typescript
// In your backend integration
this.dataService.parseScrapedData(scrapedJsonData);
```

### Toggle Events

The control panel emits console logs when toggles are activated:
- Listen for these events to trigger your scraper/buyer/seller agents
- Current implementation logs to console (ready for backend integration)

## Technologies Used

- **Angular 20.3** (latest version with signals)
- **TypeScript**
- **Chart.js** for data visualization
- **CSS3** with custom animations and gradients
- **Zoneless** Angular application for better performance

## Mock Data

The application initializes with mock data for demonstration:
- Bitcoin (BTC)
- Litecoin (LTC)
- Ethereum (ETH)
- Solana (SOL)

## Next Steps for Backend Integration

1. **WebSocket Connection**: Add real-time data streaming
2. **API Endpoints**: Connect toggle switches to backend agents
3. **Sentiment Analysis Display**: Visualize sentiment scores from sources
4. **Trading Actions**: Implement buy/sell functionality
5. **Historical Data**: Load and display historical sentiment trends

## Color Scheme

- Background: Dark gradient (#0a0a0a to #1a1a1a)
- Accent: Gold (#FFD700)
- Positive changes: Teal (#00d4aa)
- Negative changes: Red (#ff6b6b)
- Cards: Dark gray with transparency

## Responsive Design

The dashboard is fully responsive and adapts to:
- Desktop (1400px+)
- Tablet (1024px)
- Mobile (768px and below)

---

Built for CodeJam 2025 🚀

