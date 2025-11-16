const express = require('express');
const cors = require('cors');
const WebSocket = require('ws');
const chokidar = require('chokidar');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Simple health route so hitting http://localhost:3000 shows a message
app.get('/', (_req, res) => {
  res.status(200).send('Scraper backend is running. Endpoints: POST /api/scraper/start, POST /api/scraper/stop, GET /api/scraper/status, WS at /ws');
});

// Store active Python process
let scraperProcess = null;
let scraperRunning = false;

// HTTP server and WebSocket server on the same port
const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/ws' });

// Track connected clients with metadata
const connectedClients = new Set();

// Broadcast to all connected clients
function broadcast(data) {
  const payload = JSON.stringify(data);
  const clientCount = wss.clients.size;

  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });

  // Log broadcast for debugging (only for important events)
  if (data.type === 'scraper_stopped' || data.type === 'coin_data_updated') {
    console.log(`📡 Broadcasted ${data.type} to ${clientCount} client(s)`);
  }
}

// Broadcast thread-specific updates (for 3 parallel scrapers)
function broadcastThreadUpdate(threadId, message, data = {}) {
  broadcast({
    type: 'thread_update',
    threadId,
    message,
    data,
    timestamp: new Date().toISOString()
  });
}

// Watch scraped_posts.json for changes (now using analysis folder file)
const scrapedPostsPath = path.join(__dirname, '../scrapper_and_analysis/scraped_posts.json');
const coinDataPath = path.join(__dirname, '../public/coin-data.json');
const watcher = chokidar.watch(scrapedPostsPath, { persistent: true, ignoreInitial: false });

watcher.on('add', (p) => {
  console.log(`📝 File created: ${p}`);
});

watcher.on('change', (p) => {
  console.log(`📝 File changed: ${p}`);
  try {
    const data = fs.readFileSync(scrapedPostsPath, 'utf8');
    const posts = JSON.parse(data || '[]');
    broadcast({ type: 'scraper_update', data: posts, timestamp: new Date().toISOString() });
  } catch (error) {
    console.error('Error reading scraped_posts.json:', error.message);
  }
});

// API Routes (under /api)
app.post('/api/scraper/start', (_req, res) => {
  if (scraperRunning) {
    return res.json({ success: false, message: 'Scraper is already running' });
  }

  try {
    // Ensure file exists and is cleared
    fs.writeFileSync(scrapedPostsPath, '[]', 'utf8');
    console.log('🗑️  Cleared scraped_posts.json');

    // Start Python scraper
    const pythonPath = 'python3';
    const scriptPath = path.join(__dirname, '../../main.py');

    scraperProcess = spawn(pythonPath, [scriptPath], {
      cwd: path.join(__dirname, '../..'),
      env: { ...process.env },
      stdio: ['ignore', 'pipe', 'pipe']
    });

    scraperRunning = true;

    scraperProcess.stdout.on('data', (data) => {
      const message = data.toString();
      process.stdout.write(`[Scraper] ${message}`);

      // Parse thread-specific messages (e.g., "r/altcoin", "r/CryptoMoonShots", "r/pumpfun")
      const threadMatch = message.match(/r\/(altcoin|CryptoMoonShots|pumpfun)/i);
      if (threadMatch) {
        const threadId = threadMatch[1];
        broadcastThreadUpdate(threadId, message.trim());
      }

      // Always broadcast as general log too
      broadcast({ type: 'scraper_log', message, timestamp: new Date().toISOString() });

      // Detect completion phrase from main.py and trigger coin data reload broadcast
      if (/PROCESSING COMPLETE - FRONTEND UPDATED!/i.test(message)) {
        // Attempt to read coin-data.json and broadcast update event
        let coinData = [];
        try {
          if (fs.existsSync(coinDataPath)) {
            const raw = fs.readFileSync(coinDataPath, 'utf8');
            coinData = JSON.parse(raw || '[]');
          }
        } catch (e) {
          console.error('Error reading coin-data.json after processing:', e.message);
        }
        broadcast({ type: 'coin_data_updated', coins: coinData.length, timestamp: new Date().toISOString() });
      }
    });

    scraperProcess.stderr.on('data', (data) => {
      const msg = data.toString();
      process.stderr.write(`[Scraper Error] ${msg}`);
      broadcast({ type: 'scraper_log', message: msg, timestamp: new Date().toISOString() });
    });

    scraperProcess.on('close', (code) => {
      console.log(`Scraper process exited with code ${code}`);
      scraperRunning = false;
      scraperProcess = null;
      broadcast({ type: 'scraper_stopped', code, timestamp: new Date().toISOString() });

      if (code === 0) {
        console.log('✅ Scraping complete - data processed automatically by main.py');
      }
    });

    res.json({ success: true, message: 'Scraper started successfully', pid: scraperProcess.pid });
  } catch (error) {
    console.error('Error starting scraper:', error);
    res.status(500).json({ success: false, message: error.message });
  }
});

app.post('/api/scraper/stop', (_req, res) => {
  if (!scraperRunning || !scraperProcess) {
    return res.json({ success: false, message: 'Scraper is not running' });
  }
  try {
    scraperProcess.kill('SIGTERM');
    scraperRunning = false;

    // Immediately broadcast that scraper has stopped (do not trigger frontend reload yet)
    broadcast({ type: 'scraper_stopped', code: null, timestamp: new Date().toISOString() });

    // 1) Run sentiment analysis to produce sentiment.json from scraped_posts.json
    console.log('🧠 Running sentiment analysis on scraped posts...');
    const sentimentScriptPath = path.join(__dirname, '../scrapper_and_analysis/sentiment.py');

    const sentProc = spawn('python3', [sentimentScriptPath], {
      cwd: path.join(__dirname, '../scrapper_and_analysis'),
      env: { ...process.env }
    });

    // Pipe logs for visibility in backend logs and WS
    sentProc.stdout.on('data', (data) => {
      const msg = data.toString();
      process.stdout.write(`[Sentiment] ${msg}`);
      broadcast({ type: 'scraper_log', message: `[Sentiment] ${msg}`, timestamp: new Date().toISOString() });
    });

    sentProc.stderr.on('data', (data) => {
      const msg = data.toString();
      process.stderr.write(`[Sentiment Error] ${msg}`);
      broadcast({ type: 'scraper_log', message: `[Sentiment Error] ${msg}`, timestamp: new Date().toISOString() });
    });

    sentProc.on('close', (scode) => {
      if (scode !== 0) {
        console.error(`⚠️  Sentiment script exited with code ${scode}`);
        broadcast({ type: 'scraper_log', message: `⚠️  Sentiment script exited with code ${scode}`, timestamp: new Date().toISOString() });
        // We will not proceed to conversion if sentiment failed
        return;
      }

      // 2) Run conversion script to process sentiment.json into public/coin-data.json
      console.log('🔄 Running conversion script on sentiment output...');
      const convertScriptPath = path.join(__dirname, '../scrapper_and_analysis/convert_to_coin_data.py');

      const convertProcess = spawn('python3', [convertScriptPath], {
        cwd: path.join(__dirname, '../scrapper_and_analysis'),
        env: { ...process.env }
      });

      convertProcess.stdout.on('data', (data) => {
        const msg = data.toString();
        process.stdout.write(`[Convert] ${msg}`);
        broadcast({ type: 'scraper_log', message: `[Convert] ${msg}`, timestamp: new Date().toISOString() });
      });

      convertProcess.stderr.on('data', (data) => {
        const msg = data.toString();
        process.stderr.write(`[Convert Error] ${msg}`);
        broadcast({ type: 'scraper_log', message: `[Convert Error] ${msg}`, timestamp: new Date().toISOString() });
      });

      convertProcess.on('close', (code) => {
        if (code === 0) {
          console.log('✅ Conversion complete - triggering frontend update');

          // Read and broadcast updated coin data
          let coinData = [];
          try {
            if (fs.existsSync(coinDataPath)) {
              const raw = fs.readFileSync(coinDataPath, 'utf8');
              coinData = JSON.parse(raw || '[]');
            }
          } catch (e) {
            console.error('Error reading coin-data.json:', e.message);
          }

          // Broadcast coin data update AFTER conversion succeeds
          broadcast({ type: 'coin_data_updated', coins: coinData.length, timestamp: new Date().toISOString() });
        } else {
          console.error(`⚠️  Conversion script exited with code ${code}`);
          broadcast({ type: 'scraper_log', message: `⚠️  Conversion script exited with code ${code}` , timestamp: new Date().toISOString() });
        }
      });
    });

    res.json({ success: true, message: 'Scraper stopping, processing data...' });
  } catch (error) {
    console.error('Error stopping scraper:', error);
    res.status(500).json({ success: false, message: error.message });
  }
});

app.get('/api/scraper/status', (_req, res) => {
  res.json({ running: scraperRunning, pid: scraperProcess ? scraperProcess.pid : null });
});

app.get('/api/scraper/data', (_req, res) => {
  try {
    const data = fs.readFileSync(scrapedPostsPath, 'utf8');
    const posts = JSON.parse(data || '[]');
    res.json({ success: true, count: posts.length, data: posts });
  } catch (error) {
    res.json({ success: false, count: 0, data: [] });
  }
});

// WebSocket connection handler
wss.on('connection', (ws) => {
  const clientId = Date.now().toString(36) + Math.random().toString(36).substr(2);
  connectedClients.add(ws);

  console.log(`🔌 New WebSocket client connected [${clientId}] (Total: ${connectedClients.size})`);

  // Send initial data
  try {
    const data = fs.existsSync(scrapedPostsPath) ? fs.readFileSync(scrapedPostsPath, 'utf8') : '[]';
    const posts = JSON.parse(data || '[]');
    ws.send(JSON.stringify({
      type: 'initial_data',
      data: posts,
      clientId,
      timestamp: new Date().toISOString()
    }));
  } catch (error) {
    console.error('Error sending initial data:', error.message);
  }

  // Handle client messages (for future bidirectional communication)
  ws.on('message', (message) => {
    try {
      const parsed = JSON.parse(message);
      console.log(`📨 Received from client [${clientId}]:`, parsed.type || parsed);
    } catch (e) {
      console.log(`📨 Received from client [${clientId}]:`, message.toString());
    }
  });

  // Handle disconnection
  ws.on('close', () => {
    connectedClients.delete(ws);
    console.log(`🔌 Client disconnected [${clientId}] (Remaining: ${connectedClients.size})`);
  });

  // Handle errors
  ws.on('error', (error) => {
    console.error(`❌ WebSocket error [${clientId}]:`, error.message);
    connectedClients.delete(ws);
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 Backend server + WS running on http://localhost:${PORT}`);
  console.log(`🔌 WebSocket endpoint: ws://localhost:${PORT}/ws`);
  console.log(`👀 Watching scraped posts: ${scrapedPostsPath}`);
  console.log(`📁 Coin data file: ${coinDataPath}`);
});

// Cleanup on exit
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down...');
  if (scraperProcess) scraperProcess.kill('SIGTERM');
  watcher.close();
  server.close(() => process.exit(0));
});
