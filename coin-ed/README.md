# Coin'ed 🚀

**AI-Powered Cryptocurrency Sentiment Analysis Dashboard**

A modern Angular application that visualizes cryptocurrency sentiment data scraped from social media platforms (Reddit, Twitter/X) to help traders make data-driven decisions.

![Dashboard Preview](https://img.shields.io/badge/Angular-20.3-red?logo=angular)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)
![Chart.js](https://img.shields.io/badge/Chart.js-Latest-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 Project Overview

**Coin'ed** solves a critical problem for cryptocurrency traders: manually analyzing thousands of social media posts to gauge market sentiment. Our AI-powered dashboard automates this process by:

- 🌐 **Web Scraping** - Automatically scrapes Reddit, Twitter, and other platforms
- 🤖 **AI Analysis** - Analyzes sentiment from social media mentions
- 📊 **Visualization** - Displays real-time sentiment data in an intuitive dashboard
- 💰 **Smart Trading** - AI agents make buy/sell recommendations based on sentiment

---

## ✨ Features

### 🎨 Modern Dashboard
- Dark-themed, responsive UI
- Real-time cryptocurrency price tracking
- Mini charts for each coin
- Interactive full-size Chart.js visualizations

### 📈 Portfolio Management
- Track multiple cryptocurrencies
- View portfolio distribution
- Monitor total balance
- Individual coin performance metrics

### 🤖 AI Agent Controls
- **Web Scraper Toggle** - Start/stop social media scraping
- **AI Buyer Agent** - Automated buying based on sentiment
- **AI Seller Agent** - Automated selling based on sentiment

### 🔄 Dynamic Updates
- Automatic coin tab creation for new cryptocurrencies
- Real-time data updates
- Sentiment tracking from multiple sources
- Historical price charts

---

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18.x or higher
- **npm** 9.x or higher

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/coin-ed.git
cd coin-ed

# Install dependencies
npm install

# Start development server
npm start
```

Open your browser to **http://localhost:4200**

### Alternative: Use the startup script
```bash
chmod +x start.sh
./start.sh
```

---

## 📦 What's Included

```
coin-ed/
├── src/app/
│   ├── components/
│   │   ├── dashboard/          # Main container
│   │   ├── coin-card/          # Individual crypto cards
│   │   ├── portfolio/          # Portfolio sidebar
│   │   ├── chart/              # Chart.js integration
│   │   └── control-panel/      # AI agent toggles
│   ├── services/
│   │   ├── data.service.ts     # Core data management
│   │   └── data-loader.service.ts  # JSON data loading
│   └── models/
│       └── coin.model.ts       # TypeScript interfaces
├── public/
│   └── example-data.json       # Sample scraped data
└── docs/
    ├── QUICKSTART.md
    ├── INTEGRATION_GUIDE.md
    └── PROJECT_README.md
```

---

## 🎮 Demo

### Try It Out

1. **Start the application** (`npm start`)
2. **Click "📊 Load Example Scraped Data"** to see demo coins
3. **Toggle agent switches** to see controls in action
4. **Interact with the chart** - Switch timeframes and coins
5. **Check browser console** for agent events

### Sample Data

The app includes mock data for:
- Bitcoin (BTC)
- Litecoin (LTC)
- Ethereum (ETH)
- Solana (SOL)

Click the demo button to load:
- Dogecoin (DOGE)
- Shiba Inu (SHIB)

---

## 🔌 Backend Integration

This frontend is ready to connect with your backend scrapers and AI agents.

### Expected JSON Format

```json
{
  "coinId": "bitcoin",
  "name": "Bitcoin",
  "symbol": "BTC",
  "price": 52291,
  "balance": 52291,
  "changePercentage": 0.25,
  "chartData": [50000, 51000, 52000],
  "sentiment": {
    "type": "positive",
    "score": 0.85,
    "sources": [
      {
        "platform": "reddit",
        "url": "https://reddit.com/r/cryptocurrency/...",
        "text": "Bitcoin to the moon! 🚀",
        "sentiment": 0.9
      }
    ]
  }
}
```

### Integration Example

```typescript
// Send data to the frontend
this.dataService.parseScrapedData(scrapedData);
```

📖 **See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) for complete documentation**

---

## 🛠️ Tech Stack

- **Frontend Framework**: Angular 20.3 (latest)
- **Language**: TypeScript 5.x
- **Charts**: Chart.js
- **Styling**: CSS3 with custom animations
- **State Management**: Angular Signals
- **Architecture**: Standalone components, zoneless
- **SSR**: Server-Side Rendering ready

---

## 📚 Documentation

- **[START_HERE.md](./START_HERE.md)** - Complete setup guide and checklist
- **[QUICKSTART.md](./QUICKSTART.md)** - Basic usage instructions
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Backend integration with examples
- **[PROJECT_README.md](./PROJECT_README.md)** - Full technical documentation

---

## 🎨 Screenshots

### Main Dashboard
- Total balance display
- Grid of cryptocurrency cards
- Real-time price updates
- Mini charts for each coin

### Portfolio View
- Percentage distribution
- Coin breakdown
- Visual indicators

### Interactive Chart
- Multiple timeframes (1h, 3h, 1d, 1w, 1m)
- Coin selector
- Price history visualization

---

## 🧪 Development

### Available Scripts

```bash
# Start dev server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint

# Generate component
ng generate component components/my-component
```

### Code Structure

- **Components** - Standalone, reusable UI components
- **Services** - Business logic and data management
- **Models** - TypeScript interfaces and types
- **Signals** - Reactive state management

---

## 🚢 Deployment

### Build for Production

```bash
npm run build
```

Output will be in `dist/coin-ed/`

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm run build
# Upload dist/coin-ed folder to Netlify
```

### Deploy to GitHub Pages

```bash
npm install -g angular-cli-ghpages
ng build --base-href "/coin-ed/"
npx angular-cli-ghpages --dir=dist/coin-ed/browser
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🗺️ Roadmap

### Current Status (Frontend Complete ✅)
- [x] Dashboard UI
- [x] Coin cards with mini charts
- [x] Portfolio visualization
- [x] Interactive charts
- [x] Agent control toggles
- [x] JSON data parser
- [x] Documentation

### Future Development
- [ ] Backend scraper (Python/Node.js)
- [ ] Sentiment analysis AI
- [ ] Trading bot integration
- [ ] User authentication
- [ ] Historical data storage
- [ ] WebSocket real-time updates
- [ ] Mobile app (React Native)
- [ ] Browser extension

---

## 🐛 Troubleshooting

### Port 4200 already in use
```bash
lsof -ti:4200 | xargs kill -9
npm start
```

### Node modules issues
```bash
rm -rf node_modules package-lock.json
npm install
```

### Build errors
```bash
npx ng build --configuration development
# Check output for specific errors
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

Built for **CodeJam 2025** by passionate developers who believe in data-driven crypto trading.

---

## 🙏 Acknowledgments

- [Angular](https://angular.dev) - Frontend framework
- [Chart.js](https://www.chartjs.org) - Charting library
- Design inspiration from modern crypto dashboards
- CodeJam 2025 organizers

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/coin-ed/issues)
- **Documentation**: See `/docs` folder
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/coin-ed/discussions)

---

## ⭐ Star This Repo

If you find this project useful, please give it a star! It helps others discover it.

---

**Made with ❤️ for cryptocurrency enthusiasts and data-driven traders**

*Last updated: November 15, 2025*

