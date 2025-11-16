# Backend Server Quick Start

## Start Backend Server

```bash
cd /Users/muhammadaliullah/WebstormProjects/codejam2025/coin-ed/backend
node server.js
```

The server should output:
```
🚀 Backend server running on http://localhost:3000
🔌 WebSocket server running on ws://localhost:3001
👀 Watching: /path/to/scraped_posts.json
```

## Test Backend

Open another terminal:
```bash
curl http://localhost:3000/api/scraper/status
```

Should return:
```json
{"running":false,"pid":null}
```

## Troubleshooting

### "Cannot find module 'express'"
```bash
cd /Users/muhammadaliullah/WebstormProjects/codejam2025/coin-ed/backend
npm install
```

### Port already in use
```bash
# Kill existing processes
lsof -ti:3000 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

### WebSocket connection fails
1. Make sure backend is running (check console output)
2. Check browser console for errors
3. Verify ports 3000 and 3001 are not blocked by firewall

## For Demo

**Terminal 1:**
```bash
cd coin-ed/backend
node server.js
```

**Terminal 2:**
```bash
cd coin-ed
npm start
```

**Browser:**
```
http://localhost:4200
```

Then click the "AI Scraper" toggle!

