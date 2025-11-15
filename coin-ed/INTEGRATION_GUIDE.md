# Coin'ed Backend Integration Guide

## Overview
This guide explains how to integrate your web scraper and AI agents with the Coin'ed frontend.

## Architecture

### Data Flow
```
Web Scraper → JSON Data → Frontend DataService → UI Updates
     ↓
AI Agents (Buyer/Seller) → Trading Decisions
```

## JSON Data Format

### Single Coin Update
```json
{
  "coinId": "bitcoin",
  "name": "Bitcoin",
  "symbol": "BTC",
  "price": 52291,
  "balance": 52291,
  "changePercentage": 0.25,
  "feedback": "Strong buy signals on Reddit",
  "chartData": [50000, 51000, 52000, 52291],
  "icon": "₿",
  "sentiment": {
    "type": "positive",
    "score": 0.85,
    "sources": [
      {
        "platform": "reddit",
        "url": "https://reddit.com/r/cryptocurrency/...",
        "text": "Bitcoin looking bullish! Strong fundamentals.",
        "sentiment": 0.9
      },
      {
        "platform": "twitter",
        "url": "https://twitter.com/user/status/123",
        "text": "BTC breaking resistance levels",
        "sentiment": 0.8
      }
    ]
  }
}
```

### Batch Update
```json
{
  "coins": [
    { /* coin 1 data */ },
    { /* coin 2 data */ },
    { /* coin 3 data */ }
  ]
}
```

## Integration Methods

### Method 1: HTTP POST (Recommended for periodic updates)

```python
# Python example using requests
import requests
import json

def send_scraped_data(coin_data):
    url = "http://localhost:4200/api/update"  # Your backend endpoint
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(coin_data), headers=headers)
    return response.json()

# Example usage
coin_data = {
    "coinId": "dogecoin",
    "name": "Dogecoin",
    "symbol": "DOGE",
    "price": 0.08,
    "balance": 15000,
    "changePercentage": 0.15,
    "feedback": "Trending on Reddit",
    "sentiment": {
        "type": "positive",
        "score": 0.75,
        "sources": [...]
    }
}

send_scraped_data(coin_data)
```

### Method 2: WebSocket (Recommended for real-time updates)

```python
# Python WebSocket server example
import asyncio
import websockets
import json

async def send_updates(websocket):
    while True:
        # Your scraping logic here
        coin_data = scrape_reddit_and_twitter()
        
        # Send to frontend
        await websocket.send(json.dumps(coin_data))
        
        # Wait before next update
        await asyncio.sleep(60)  # Update every minute

async def main():
    async with websockets.serve(send_updates, "localhost", 8765):
        await asyncio.Future()  # run forever

asyncio.run(main())
```

### Method 3: File Watching (Development/Testing)

```python
# Python file watcher example
import json
import time

def update_data_file(coin_data):
    with open('public/example-data.json', 'w') as f:
        json.dump({"coins": coin_data}, f, indent=2)

# The frontend can poll this file or use file watchers
```

## Frontend Integration Points

### 1. DataService Methods

```typescript
// In your Angular service or component:
import { DataService } from './services/data.service';
import { DataLoaderService } from './services/data-loader.service';

// Method 1: Parse JSON directly
this.dataService.parseScrapedData(jsonData);

// Method 2: Load from file/URL
this.dataLoaderService.loadFromFile('/api/coins');

// Method 3: Simulate incoming data
this.dataLoaderService.simulateIncomingData(coinData);
```

### 2. Control Panel Events

The toggles in the control panel can trigger your backend agents:

```typescript
// In control-panel.component.ts, add HTTP calls:
import { HttpClient } from '@angular/common/http';

onScraperToggle(): void {
  this.dataService.toggleScraper();
  const enabled = this.dataService.agentControls().scraperEnabled;
  
  // Call your backend
  this.http.post('/api/scraper/toggle', { enabled }).subscribe();
}

onBuyerToggle(): void {
  this.dataService.toggleBuyer();
  const enabled = this.dataService.agentControls().buyerEnabled;
  
  // Call your backend
  this.http.post('/api/buyer/toggle', { enabled }).subscribe();
}

onSellerToggle(): void {
  this.dataService.toggleSeller();
  const enabled = this.dataService.agentControls().sellerEnabled;
  
  // Call your backend
  this.http.post('/api/seller/toggle', { enabled }).subscribe();
}
```

## Sentiment Data Structure

### Platforms Supported
- `reddit` - Reddit posts and comments
- `twitter` - Twitter/X posts
- `other` - Other social media platforms

### Sentiment Types
- `positive` - Bullish sentiment (score 0.6-1.0)
- `neutral` - Mixed signals (score 0.4-0.6)
- `negative` - Bearish sentiment (score 0.0-0.4)

### Example Scraper Output

```python
# Reddit scraper example
def scrape_reddit_sentiment(subreddit, coin_symbol):
    import praw
    
    reddit = praw.Reddit(...)
    posts = reddit.subreddit(subreddit).hot(limit=100)
    
    sentiment_sources = []
    for post in posts:
        if coin_symbol.lower() in post.title.lower():
            sentiment_score = analyze_sentiment(post.title + post.selftext)
            sentiment_sources.append({
                "platform": "reddit",
                "url": f"https://reddit.com{post.permalink}",
                "text": post.title,
                "sentiment": sentiment_score
            })
    
    avg_sentiment = sum(s['sentiment'] for s in sentiment_sources) / len(sentiment_sources)
    
    return {
        "coinId": coin_symbol.lower(),
        "sentiment": {
            "type": "positive" if avg_sentiment > 0.6 else "neutral" if avg_sentiment > 0.4 else "negative",
            "score": avg_sentiment,
            "sources": sentiment_sources[:10]  # Top 10 sources
        }
    }
```

## Backend API Endpoints to Implement

### 1. Scraper Control
```
POST /api/scraper/toggle
Body: { "enabled": true/false }
Response: { "status": "started/stopped" }
```

### 2. Buyer Agent Control
```
POST /api/buyer/toggle
Body: { "enabled": true/false }
Response: { "status": "started/stopped" }
```

### 3. Seller Agent Control
```
POST /api/seller/toggle
Body: { "enabled": true/false }
Response: { "status": "started/stopped" }
```

### 4. Data Update Endpoint
```
POST /api/coins/update
Body: Single coin object or { "coins": [...] }
Response: { "success": true, "coinsUpdated": 3 }
```

### 5. Get Current Data
```
GET /api/coins
Response: { "coins": [...] }
```

## Chart Data Format

Chart data should be an array of price points:
```json
"chartData": [
  38000, 38100, 38050, 38200, 38150, 38300, 38250, 38400,
  38350, 38500, 38450, 38600, 38550, 38700, 38650, 38800
]
```

- Minimum 10 points recommended
- Maximum 100 points for performance
- Points should represent equally-spaced time intervals

## Testing Your Integration

### 1. Test with example-data.json
Click the "Load Example Scraped Data" button in the dashboard to see how data updates work.

### 2. Test with curl
```bash
# Test single coin update
curl -X POST http://localhost:4200/api/update \
  -H "Content-Type: application/json" \
  -d '{
    "coinId": "test-coin",
    "name": "Test Coin",
    "symbol": "TEST",
    "price": 100,
    "balance": 1000,
    "changePercentage": 0.05
  }'
```

### 3. Monitor Browser Console
All data updates are logged to the browser console for debugging.

## Best Practices

1. **Rate Limiting**: Don't update more than once per minute to avoid UI performance issues
2. **Batch Updates**: Send multiple coins in one request when possible
3. **Error Handling**: Always include error handling in your scrapers
4. **Data Validation**: Validate data before sending to frontend
5. **Timestamps**: Include timestamps for tracking data freshness
6. **Source Attribution**: Always include source URLs for transparency

## Security Considerations

1. **API Keys**: Never expose API keys in frontend code
2. **CORS**: Configure CORS properly for production
3. **Rate Limiting**: Implement rate limiting on backend endpoints
4. **Authentication**: Add authentication for production deployment
5. **Data Sanitization**: Sanitize scraped text to prevent XSS

## Deployment

### Development
```bash
npm start
# Frontend runs on http://localhost:4200
```

### Production
```bash
npm run build
# Deploy dist/coin-ed folder to your web server
```

## Troubleshooting

### Data not updating?
- Check browser console for errors
- Verify JSON format matches specification
- Ensure CORS is configured correctly

### Toggle switches not working?
- Verify backend endpoints are accessible
- Check network tab for failed requests
- Ensure HttpClient is properly configured

### Charts not displaying?
- Verify chartData is an array of numbers
- Check that at least 2 data points exist
- Look for Chart.js errors in console

## Support

For questions or issues, check:
- PROJECT_README.md for general information
- Browser developer console for runtime errors
- Network tab for API call issues

---

Happy coding! 🚀

