# helloCoin'ed - Complete Project Workflow
## End-to-End System Architecture & Communication Flow

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Startup Sequence](#system-startup-sequence)
3. [Complete Scraping Workflow](#complete-scraping-workflow)
4. [Data Processing Pipeline](#data-processing-pipeline)
5. [Frontend Update Mechanism](#frontend-update-mechanism)
6. [Real-time Communication Flow](#real-time-communication-flow)
7. [Complete User Journey](#complete-user-journey)
8. [Technical Deep Dive](#technical-deep-dive)

---

## 🎯 Project Overview

### **What is helloCoin'ed?**
A real-time cryptocurrency sentiment analysis platform that:
- Scrapes social media (Reddit) for memecoin discussions
- Analyzes sentiment using AI/NLP
- Fetches real-time price & metadata from blockchain APIs
- Displays interactive dashboard with BUY/HOLD/SELL recommendations
- Provides live scraper logs and automated data updates

### **Technology Stack**
- **Frontend**: Angular 18 + TypeScript + RxJS Signals
- **Backend**: Node.js + Express + WebSocket
- **Scraping**: Python + Browser Cash API (headless browser automation)
- **Sentiment Analysis**: Python NLP libraries
- **APIs**: Moralis (Solana), DexScreener, Jupiter (token metadata/prices)
- **Real-time Communication**: WebSocket for bidirectional streaming
- **Data Storage**: JSON files (scraped_posts.json, sentiment.json, coin-data.json)

---

## 🚀 System Startup Sequence

### **Step 1: Backend Server Initialization**

```bash
cd coin-ed/backend
node server.js
```

**What Happens:**

1. **Express HTTP Server Creation**
   ```javascript
   const app = express();
   const server = http.createServer(app);
   ```
   - Creates HTTP server listening on port 3000
   - Registers middleware: CORS, JSON body parser
   - Sets up REST API routes

2. **WebSocket Server Attachment**
   ```javascript
   const wss = new WebSocket.Server({ server, path: '/ws' });
   ```
   - Attaches WebSocket server to same HTTP server
   - WebSocket endpoint: `ws://localhost:3000/ws`
   - Enables real-time bidirectional communication

3. **File Watcher Setup**
   ```javascript
   const watcher = chokidar.watch('scraped_posts.json', { persistent: true });
   ```
   - Monitors `scrapper_and_analysis/scraped_posts.json` for changes
   - Triggers WebSocket broadcast when file is modified
   - Instant synchronization between file system and clients

4. **Process State Initialization**
   ```javascript
   let scraperProcess = null;
   let scraperRunning = false;
   ```
   - Tracks Python scraper process
   - Prevents multiple concurrent scraper instances
   - Manages process lifecycle

**Backend Ready State:**
```
🚀 Backend server + WS running on http://localhost:3000
🔌 WebSocket endpoint: ws://localhost:3000/ws
👀 Watching scraped posts: /path/to/scraped_posts.json
📁 Coin data file: /path/to/coin-data.json
```

---

### **Step 2: Frontend Application Launch**

```bash
cd coin-ed
npm start
# or: ng serve
```

**Angular Initialization Sequence:**

1. **Main Entry Point** (`main.ts`)
   ```typescript
   bootstrapApplication(AppComponent, appConfig)
   ```
   - Loads Angular application
   - Initializes dependency injection
   - Starts change detection

2. **App Component Loads** (`app.ts`)
   ```typescript
   <router-outlet />  // Renders DashboardComponent
   ```
   - Routes to `/` → DashboardComponent
   - Initializes all services (DataService, ScraperService)

3. **Services Auto-Initialize**
   
   **a) DataService Constructor**
   ```typescript
   constructor() {
     this.loadCoinData();  // Load existing coin-data.json
     this.subscribeToScraperUpdates();
     this.listenForCoinDataEvents();
   }
   ```
   - Fetches `public/coin-data.json` on load
   - Subscribes to scraper data stream
   - Listens for `coin-data-updated` custom events

   **b) ScraperService Constructor**
   ```typescript
   constructor(@Inject(PLATFORM_ID) platformId: Object) {
     if (isPlatformBrowser(platformId)) {
       this.connectWebSocket();  // ← KEY: Establishes WS connection
       this.checkStatus();       // ← Polls scraper status
     }
   }
   ```

4. **WebSocket Connection Established**
   ```typescript
   const url = 'ws://localhost:3000/ws';
   this.ws = new WebSocket(url);
   
   this.ws.onopen = () => {
     console.log('[WebSocket] Connected successfully');
     this.connectedSubject.next(true);
   };
   ```
   - Frontend connects to backend WebSocket
   - Backend sends initial data immediately

5. **Initial Data Received**
   ```typescript
   // Backend sends on connection
   ws.send(JSON.stringify({
     type: 'initial_data',
     data: existingPosts,
     clientId: '...'
   }));
   
   // Frontend receives
   case 'initial_data':
     this.scraperDataSubject.next(update.data);
     this.addLog(`Initial scraped posts loaded (${update.data.length})`);
   ```

6. **Dashboard Renders**
   - Displays coin cards from `coin-data.json`
   - Shows empty state if no data
   - Control panel shows scraper status (OFF initially)
   - Live logs show "✅ Connected to scraper backend"

**Frontend Ready State:**
```
✅ Angular app running on http://localhost:4200
✅ WebSocket connected to backend
✅ Coin data loaded (if exists)
✅ Ready for user interaction
```

---

## 🔍 Complete Scraping Workflow

### **Phase 1: User Initiates Scraping**

#### **Step 1: User Clicks "AI Web Scraper" Toggle**

**Frontend (Dashboard Component):**
```typescript
// User clicks toggle in control-panel.component
toggleScraper() {
  this.dataService.toggleScraper();  // Calls DataService method
}
```

**DataService:**
```typescript
async toggleScraper() {
  const newState = !this.agentControls().scraperEnabled;
  
  if (newState) {
    const success = await this.scraperService.startScraper();
    if (success) {
      this.agentControls.set({ scraperEnabled: true });
    }
  }
}
```

**ScraperService:**
```typescript
async startScraper(): Promise<boolean> {
  // HTTP POST to backend
  const res = await fetch('http://localhost:3000/api/scraper/start', {
    method: 'POST'
  });
  const result = await res.json();
  
  if (result.success) {
    this.scraperStatusSubject.next({ running: true, pid: result.pid });
    this.addLog('Scraper started successfully');
    return true;
  }
}
```

**HTTP Request Sent:**
```http
POST http://localhost:3000/api/scraper/start
Content-Type: application/json
```

---

#### **Step 2: Backend Receives Start Request**

**Backend (`server.js`):**
```javascript
app.post('/api/scraper/start', (req, res) => {
  if (scraperRunning) {
    return res.json({ success: false, message: 'Already running' });
  }
  
  try {
    // 1. Clear previous data
    fs.writeFileSync(scrapedPostsPath, '[]', 'utf8');
    console.log('🗑️  Cleared scraped_posts.json');
    
    // 2. Spawn Python scraper process
    const pythonPath = 'python3';
    const scriptPath = path.join(__dirname, '../../main.py');
    
    scraperProcess = spawn(pythonPath, ['-u', scriptPath], {
      cwd: path.join(__dirname, '../..'),
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
      stdio: ['ignore', 'pipe', 'pipe']
    });
    
    scraperRunning = true;
    
    // 3. Setup output listeners (see Step 3)
    // ...
    
    // 4. Send success response
    res.json({ 
      success: true, 
      pid: scraperProcess.pid 
    });
    
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});
```

**Backend Console Output:**
```
🗑️  Cleared scraped_posts.json
[Scraper] 🚀 Starting 3 Parallel Memecoin Sentiment Scrapers...
[Scraper] 📋 Scraping: r/altcoin, r/CryptoMoonShots, r/pumpfun
```

---

#### **Step 3: Python Scraper Process Starts**

**Backend Captures Python Output:**
```javascript
scraperProcess.stdout.on('data', (data) => {
  const message = data.toString();
  
  // 1. Log to backend console
  process.stdout.write(`[Scraper] ${message}`);
  
  // 2. Detect thread-specific messages
  const threadMatch = message.match(/r\/(altcoin|CryptoMoonShots|pumpfun)/i);
  if (threadMatch) {
    broadcastThreadUpdate(threadMatch[1], message.trim());
  }
  
  // 3. Broadcast all logs via WebSocket
  broadcast({ 
    type: 'scraper_log', 
    message, 
    timestamp: new Date().toISOString() 
  });
});
```

**WebSocket Broadcast:**
```javascript
function broadcast(data) {
  const payload = JSON.stringify(data);
  wss.clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(payload);
    }
  });
}
```

---

### **Phase 2: Active Scraping**

#### **Step 4: Python Scraper Executes** (`main.py`)

**Main Script Flow:**
```python
def main():
    # 1. Initialize 3 parallel scrapers
    scrapers = [
        ('r/altcoin', RedditScraper()),
        ('r/CryptoMoonShots', RedditScraper()),
        ('r/pumpfun', RedditScraper())
    ]
    
    # 2. Run in parallel threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for subreddit, scraper in scrapers:
            future = executor.submit(
                scraper.scrape_subreddit,
                subreddit,
                limit_per_subreddit=10,
                scrape_comments=True
            )
            futures.append(future)
        
        # Wait for all to complete
        for future in as_completed(futures):
            posts = future.result()
    
    # 3. Save to JSON
    scraper.to_json(all_posts, 'scraped_posts.json')
```

**For Each Subreddit Thread:**

1. **Browser Cash Session Start**
   ```python
   self.client.start_session()  # Opens headless Chrome
   ```
   - Connects to Browser Cash API
   - Opens browser instance
   - Gets CDP (Chrome DevTools Protocol) URL

2. **Navigate to Reddit**
   ```python
   self.navigate_to_subreddit(subreddit, sort="new")
   # → https://www.reddit.com/r/altcoin/new/
   ```
   - Uses Browser Cash API to navigate
   - Waits 5 seconds for page load
   - Refreshes page (bypasses bot detection)

3. **Scrape Post Listings**
   ```python
   page_posts = self.scrape_posts(subreddit, limit=25)
   ```
   - Executes JavaScript in browser context
   - Queries `shreddit-post` elements
   - Extracts: title, score, comments, timestamp, author, link
   - Filters: Only posts from last 14 days

4. **For Each Post: Scrape Comments**
   ```python
   if post.comment_count > 0:
       comments = self.scrape_comments(post.link, limit=10)
       post.comments = comments
   ```
   - Navigates to post URL
   - Waits 7 seconds for comments to load
   - Queries `shreddit-comment` elements
   - Extracts comment text (removes UI noise)
   - Navigates back to subreddit listing

5. **Token Identification (Async)**
   ```python
   def _start_token_identification_async(post):
       # 1. Check title for $TOKEN pattern
       token = extract_token_from_title(post.title)
       
       if not token:
           # 2. Use Agent API for AI token identification
           token = agent_client.identify_token_name(
               post.title + " " + post.content
           )
       
       post.token_name = token
       update_post_in_json(post)
   ```
   - Background thread per post
   - Global semaphore limits concurrent API calls
   - Updates JSON file as tokens are identified

6. **Scroll & Load More Posts**
   ```python
   for _ in range(10):
       self.client.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
       time.sleep(1.5)
   ```
   - Triggers Reddit's infinite scroll
   - Loads additional posts
   - Repeats until posts older than 14 days found

7. **Stop Conditions**
   - Post older than 14 days encountered
   - 3 minutes elapsed (timeout)
   - Page limit reached (50 pages max)

**Real-time Output (every step):**
```
[Scraper] 🔍 Scraping r/altcoin (past week)...
[Scraper] 📄 Scraping page 1...
[Scraper] 📊 Scraped 25 posts
[Scraper] 📝 Scraping comments for post 1 (has 12 comments)...
[Scraper] ✅ Extracted 12 comments
[Scraper] 🤖 Starting token identification for post 1...
[Scraper] ✅ Found token in title for post 1: PEP
[Scraper] 💾 Saved 47 total posts to scraped_posts.json
```

---

#### **Step 5: File Watcher Detects Changes**

**Every time `scraped_posts.json` is updated:**

```javascript
// Backend file watcher
watcher.on('change', (path) => {
  console.log(`📝 File changed: ${path}`);
  
  try {
    const data = fs.readFileSync(scrapedPostsPath, 'utf8');
    const posts = JSON.parse(data || '[]');
    
    // Broadcast to all connected clients
    broadcast({ 
      type: 'scraper_update', 
      data: posts, 
      timestamp: new Date().toISOString() 
    });
  } catch (error) {
    console.error('Error reading file:', error.message);
  }
});
```

**Frontend Receives Update:**
```typescript
case 'scraper_update':
  this.scraperDataSubject.next(update.data);
  this.addLog(`Received ${update.data.length} posts from scraper`);
  break;
```

**Result:** Live scraper logs update in real-time as posts are scraped!

---

#### **Step 6: Frontend Displays Live Logs**

**ScraperLogsComponent:**
```typescript
logs = toSignal(this.scraperService.scraperLogs$);

// Auto-scroll effect
effect(() => {
  this.logs();  // Triggers on signal change
  setTimeout(() => this.scrollToBottom(), 0);
});
```

**User Sees:**
```
[10:14:32 AM] ✅ Connected to scraper backend
[10:14:35 AM] Scraper started successfully
[10:14:36 AM] [Scraper] 🚀 Starting 3 Parallel Memecoin Sentiment Scrapers...
[10:14:37 AM] [altcoin] 🔍 Scraping r/altcoin (past week)...
[10:14:40 AM] [CryptoMoonShots] 📊 Scraped 25 posts
[10:14:42 AM] [pumpfun] 📝 Scraping comments for post 3...
[10:14:45 AM] [altcoin] ✅ Found token in title: HEGE
```

**Every log line:**
1. Generated by Python `print()` statement
2. Captured by Node.js child process stdout
3. Broadcast via WebSocket
4. Received by Angular ScraperService
5. Added to logs array (RxJS BehaviorSubject)
6. Converted to Signal via `toSignal()`
7. Angular effect triggers scroll
8. UI updates instantly (auto-scroll to bottom)

---

### **Phase 3: Scraping Completes**

#### **Step 7: Python Script Finishes**

**All 3 threads complete:**
```python
print("✅ All scrapers completed!")
print(f"Total posts scraped: {len(all_posts)}")

# Save final JSON
scraper.to_json(all_posts, 'scraped_posts.json')

# Exit cleanly
sys.exit(0)
```

**Backend Detects Process Exit:**
```javascript
scraperProcess.on('close', (code) => {
  console.log(`Scraper process exited with code ${code}`);
  
  scraperRunning = false;
  scraperProcess = null;
  
  // Broadcast to frontend
  broadcast({ 
    type: 'scraper_stopped', 
    code, 
    timestamp: new Date().toISOString() 
  });
  
  if (code === 0) {
    console.log('✅ Scraping complete - processing data...');
    // Data processing starts automatically (see Phase 4)
  }
});
```

**Frontend Updates Status:**
```typescript
case 'scraper_stopped':
  this.scraperStatusSubject.next({ running: false, pid: null });
  this.addLog('Scraper stopped');
  break;
```

**User Sees:**
- Scraper toggle turns OFF
- Final log: "Scraper stopped"
- Processing begins automatically

---

## 📊 Data Processing Pipeline

### **Phase 4: Automated Post-Processing**

**This happens when user clicks scraper OFF, or scraper auto-completes.**

#### **Step 8: Sentiment Analysis Triggered**

**Backend (`server.js` in `/api/scraper/stop` route):**
```javascript
// 1. Kill scraper process (if running)
if (scraperProcess) {
  scraperProcess.kill('SIGTERM');
}

// 2. Run sentiment analysis
console.log('🧠 Running sentiment analysis...');
const sentimentScript = path.join(__dirname, '../scrapper_and_analysis/sentiment.py');

const sentProc = spawn('python3', ['-u', sentimentScript], {
  cwd: path.join(__dirname, '../scrapper_and_analysis'),
  env: { ...process.env, PYTHONUNBUFFERED: '1' }
});

// 3. Stream logs to frontend
sentProc.stdout.on('data', (data) => {
  const msg = data.toString();
  process.stdout.write(`[Sentiment] ${msg}`);
  broadcast({ 
    type: 'scraper_log', 
    message: `[Sentiment] ${msg}` 
  });
});
```

**Sentiment Script Executes** (`sentiment.py`):

```python
# 1. Load scraped posts
with open('scraped_posts.json', 'r') as f:
    posts = json.load(f)

# 2. Group by token
tokens = {}
for post in posts:
    token = post.get('token_name')
    if token:
        if token not in tokens:
            tokens[token] = []
        tokens[token].append(post)

# 3. Calculate sentiment for each token
for token, token_posts in tokens.items():
    # Analyze title, content, comments
    raw_sentiment = analyze_text_sentiment(post.title + " " + post.content)
    
    # Weight by upvotes & comment count
    aggregate_sentiment = calculate_aggregate(
        raw_sentiment, 
        post.upvotes_likes, 
        post.comment_count
    )
    
    # Engagement score
    engagement = calculate_engagement(
        post.comment_count,
        post.upvotes_likes,
        len(token_posts)
    )
    
    # Confidence & recommendation
    confidence = calculate_confidence(
        raw_sentiment,
        aggregate_sentiment,
        engagement
    )
    
    recommendation = "BUY" if confidence >= 0.75 else "HOLD" if confidence >= 0.55 else "SELL"
    
    # Save to sentiment.json
    sentiment_data.append({
        'token': token,
        'raw_sentiment_score': raw_sentiment,
        'aggregate_sentiment_score': aggregate_sentiment,
        'engagement_score': engagement,
        'confidence': confidence,
        'recommendation': recommendation,
        'posts': token_posts
    })

# 4. Write sentiment.json
with open('sentiment.json', 'w') as f:
    json.dump(sentiment_data, f, indent=2)

print(f"✅ Sentiment analysis complete for {len(tokens)} tokens")
```

**User Sees Live Output:**
```
[Sentiment] ============================================================
[Sentiment] 🧠 SENTIMENT ANALYSIS STARTING
[Sentiment] 📊 Total posts loaded: 47
[Sentiment] 🔍 Processing post 1/47 - Token: PEP
[Sentiment]    💬 Comments analyzed: 12
[Sentiment]    📈 Raw sentiment: 0.753
[Sentiment]    ✅ Aggregate sentiment: 0.821
[Sentiment] ✅ Analysis complete for 12 tokens
```

---

#### **Step 9: Token Metadata Fetching**

**Backend Continues Pipeline:**
```javascript
sentProc.on('close', (scode) => {
  if (scode !== 0) {
    console.error('Sentiment failed!');
    return;
  }
  
  // Run conversion script
  console.log('🔄 Running conversion script...');
  const convertScript = path.join(__dirname, '../scrapper_and_analysis/convert_to_coin_data.py');
  
  const convertProc = spawn('python3', ['-u', convertScript], {
    cwd: path.join(__dirname, '../scrapper_and_analysis'),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });
  
  // Stream logs
  convertProc.stdout.on('data', (data) => {
    const msg = data.toString();
    process.stdout.write(`[Convert] ${msg}`);
    broadcast({ 
      type: 'scraper_log', 
      message: `[Convert] ${msg}` 
    });
  });
});
```

**Conversion Script** (`convert_to_coin_data.py`):

```python
# 1. Load sentiment.json
with open('sentiment.json', 'r') as f:
    sentiment_data = json.load(f)

# 2. For each token, fetch metadata
coin_data = []
for token_entry in sentiment_data:
    token = token_entry['token']
    
    print(f"[{i}/{total}] 🪙 Processing: {token}")
    
    # 3. Try DexScreener first
    print(f"🔍 Searching DexScreener for {token} on Solana...")
    dex_data = search_dexscreener(token, 'solana')
    
    if dex_data:
        price = dex_data['price']
        address = dex_data['address']
        change_24h = dex_data['change_24h']
        logo = dex_data['logo']
        
        print(f"💰 Price from DexScreener: ${price}")
        print(f"📈 24h Change: {change_24h}%")
        print(f"📍 Token Address: {address}")
    
    # 4. If no logo, try Jupiter
    if not logo:
        print(f"🔄 No logo from DexScreener, trying Jupiter...")
        jupiter_logo = get_jupiter_logo(address)
        if jupiter_logo:
            logo = jupiter_logo
            print(f"✅ Found logo in Jupiter")
    
    # 5. If still no logo, try Moralis
    if not logo:
        print(f"🔄 Trying Moralis...")
        moralis_data = get_moralis_metadata(address)
        if moralis_data and moralis_data.get('logo'):
            logo = moralis_data['logo']
            print(f"✅ Found logo in Moralis")
    
    # 6. Build coin data object
    coin = {
        'id': token.lower(),
        'name': token,
        'symbol': token,
        'address': address,
        'price': price,
        'balance': price,  # For demo
        'logo': logo,
        'chain': 'solana',
        'decimals': 9,
        'changePercentage': change_24h,
        'raw_sentiment_score': token_entry['raw_sentiment_score'],
        'aggregate_sentiment_score': token_entry['aggregate_sentiment_score'],
        'engagement_score': token_entry['engagement_score'],
        'confidence': token_entry['confidence'],
        'recommendation': token_entry['recommendation'],
        # Include latest post for details
        'title': token_entry['posts'][0]['title'],
        'content': token_entry['posts'][0]['content'],
        'author': token_entry['posts'][0]['author'],
        'comments': token_entry['posts'][0]['comments'],
        # ... other post fields
    }
    
    coin_data.append(coin)

# 7. Write to public/coin-data.json
output_path = '../public/coin-data.json'
with open(output_path, 'w') as f:
    json.dump(coin_data, f, indent=2)

print(f"✅ Coin data saved: {len(coin_data)} coins")
print(f"📊 Logos found: {logos_found}/{len(coin_data)}")
print("🎉 PROCESSING COMPLETE - FRONTEND UPDATED!")
```

**User Sees API Calls in Real-time:**
```
[Convert] [1/12] 🪙 Processing: PEP
[Convert]    🔍 Searching DexScreener for PEP on Solana...
[Convert]    📡 DexScreener API Status: 200
[Convert]    💰 Price from DexScreener: $0.00251900
[Convert]    📈 24h Change: -0.01%
[Convert]    📍 Token Address: GJAFwWjJ3vnTsrQVabjBVK2TYB1YtRCQXRDfDgUnpump
[Convert]    🔄 No logo from DexScreener, trying Jupiter...
[Convert]    ✅ Found logo in Jupiter: https://cf-ipfs.com/ipfs/...
[Convert] [2/12] 🪙 Processing: HEGE
[Convert]    🔍 Searching DexScreener for HEGE on Solana...
```

---

#### **Step 10: Frontend Update Triggered**

**Backend Detects Completion:**
```javascript
convertProc.on('close', (code) => {
  if (code === 0) {
    console.log('✅ Conversion complete - triggering frontend update');
    
    // Read final coin data
    const coinData = JSON.parse(fs.readFileSync(coinDataPath, 'utf8'));
    
    // Broadcast update event
    broadcast({ 
      type: 'coin_data_updated', 
      coins: coinData.length, 
      timestamp: new Date().toISOString() 
    });
  }
});
```

**Frontend Receives Event:**
```typescript
case 'coin_data_updated':
  this.addLog(`✅ Coin data updated (${update.coins || 0} coins)`);
  
  // Dispatch custom event to trigger reload
  window.dispatchEvent(new CustomEvent('coin-data-updated'));
  break;
```

**DataService Listens for Event:**
```typescript
// In constructor
if (typeof window !== 'undefined') {
  window.addEventListener('coin-data-updated', () => {
    console.log('🔄 Reloading coin data after update event');
    this.loadCoinData();  // Re-fetch coin-data.json
  });
}
```

**LoadCoinData Method:**
```typescript
private async loadCoinData(): Promise<void> {
  try {
    const baseUrl = window.location.origin;
    const ts = Date.now();  // Cache busting
    
    // Fetch with no-cache
    const response = await fetch(`${baseUrl}/coin-data.json?ts=${ts}`, { 
      cache: 'no-store' 
    });
    
    const coinDataArray = await response.json();
    
    // Map to Coin model
    const coins: Coin[] = coinDataArray.map((item: any) => ({
      id: item.id,
      name: item.name,
      symbol: item.symbol,
      address: item.address,
      price: item.price,
      logo: item.logo,
      // ... all other fields
      hype: item.raw_sentiment_score,
      communityHype: item.aggregate_sentiment_score,
      popularity: item.engagement_score,
      confidence: item.confidence,
      recommendation: item.recommendation,
      latestPost: this.extractPostData(item)
    }));
    
    // Update reactive signal
    this.coins.set(coins);
    
    // Recalculate portfolio
    this.updatePortfolio();
    
    console.log(`✅ Loaded ${coins.length} coins`);
  } catch (error) {
    console.error('Error loading coin data:', error);
  }
}
```

---

## 🎨 Frontend Update Mechanism

### **Phase 5: Dashboard Refresh**

#### **Step 11: UI Updates Reactively**

**Angular Signals Propagation:**

```typescript
// 1. Signal update triggers change detection
this.coins.set(newCoins);  // ← Signal updated

// 2. Any component using this signal auto-updates
@Component({
  template: `
    @for (coin of dataService.coins(); track coin.id) {
      <app-coin-card [coin]="coin"></app-coin-card>
    }
  `
})
```

**What Changes on Dashboard:**

1. **Coin Cards Grid**
   - New coins appear (if new tokens discovered)
   - Existing coins update (price, sentiment, recommendation)
   - Cards show: logo, name, price, 24h change, confidence %
   - Recommendation badge: BUY (green), HOLD (yellow), SELL (red)

2. **Left Sidebar**
   - Recently updated coins move to top
   - "NEW" badge shows for 5 seconds
   - Coin count updates: "Tracked Coins: 12"
   - Logos load from fetched URLs

3. **Total Balance**
   - Recalculated: Σ(price × balance) for all coins
   - Updates in header: "$154,610.00"

4. **Sentiment Gauges**
   - Hype gauge: raw_sentiment_score
   - Community gauge: aggregate_sentiment_score
   - Popularity gauge: engagement_score
   - Overall Confidence bar updates

5. **Latest Post Display**
   - When coin selected, shows Reddit post details
   - Title, content, author, timestamp
   - Comments list (scrollable)
   - Source link

**Reactive Update Chain:**
```
coin-data.json updated
    ↓
DataService.loadCoinData()
    ↓
this.coins.set(newCoins)
    ↓
Angular Signal change detection
    ↓
All components using coins() signal re-render
    ↓
User sees updated dashboard instantly
```

---

## 🔄 Real-time Communication Flow

### **Complete Message Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERACTION                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Click "Start Scraper"
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  ANGULAR FRONTEND (PORT 4200)                │
│                                                               │
│  1. Control Panel Component                                  │
│     toggleScraper() → DataService.toggleScraper()            │
│                                                               │
│  2. ScraperService                                           │
│     startScraper() → HTTP POST /api/scraper/start            │
│                                                               │
│  3. WebSocket Connection                                     │
│     ws://localhost:3000/ws (OPEN)                            │
│     - onmessage: handleUpdate()                              │
│     - logs$, status$, data$ (RxJS observables)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP POST
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               NODE.JS BACKEND (PORT 3000)                    │
│                                                               │
│  1. Express Route: POST /api/scraper/start                   │
│     - Clear scraped_posts.json                               │
│     - Spawn Python scraper process                           │
│     - Return { success: true, pid: 12345 }                   │
│                                                               │
│  2. Child Process Listeners                                  │
│     scraperProcess.stdout.on('data') →                       │
│       - Log to console                                       │
│       - broadcast({ type: 'scraper_log', message })          │
│                                                               │
│  3. File Watcher (Chokidar)                                  │
│     watcher.on('change') →                                   │
│       - Read scraped_posts.json                              │
│       - broadcast({ type: 'scraper_update', data: posts })   │
│                                                               │
│  4. WebSocket Server                                         │
│     - Maintains set of connected clients                     │
│     - broadcast() sends to all clients                       │
│     - JSON.stringify messages                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ spawn child process
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   PYTHON SCRAPER (main.py)                   │
│                                                               │
│  1. Initialize 3 parallel threads                            │
│     - Thread 1: r/altcoin                                    │
│     - Thread 2: r/CryptoMoonShots                            │
│     - Thread 3: r/pumpfun                                    │
│                                                               │
│  2. Each thread:                                             │
│     a. Connect to Browser Cash API                           │
│     b. Open headless Chrome instance                         │
│     c. Navigate to reddit.com/r/{subreddit}/new/             │
│     d. Scrape post listings (title, score, comments)         │
│     e. Click on posts with comments                          │
│     f. Scrape comment text                                   │
│     g. Identify token names ($TOKEN or AI)                   │
│     h. Write to scraped_posts.json (incremental)             │
│                                                               │
│  3. Output to stdout (unbuffered)                            │
│     print("🔍 Scraping r/altcoin...", flush=True)            │
│     → Captured by Node.js → Sent via WebSocket               │
│                                                               │
│  4. On completion:                                           │
│     sys.exit(0) → Triggers 'close' event in Node.js          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ writes to
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FILE SYSTEM (JSON FILES)                   │
│                                                               │
│  scraped_posts.json                                          │
│  ├─ Post 1: { title, content, token_name, comments: [...] }  │
│  ├─ Post 2: { ... }                                          │
│  └─ Post N: { ... }                                          │
│                                                               │
│  [Chokidar detects change] → Triggers WebSocket broadcast    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Process exit triggers pipeline
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              SENTIMENT ANALYSIS (sentiment.py)               │
│                                                               │
│  1. Read scraped_posts.json                                  │
│  2. Group posts by token_name                                │
│  3. For each token:                                          │
│     - Analyze sentiment (title + content + comments)         │
│     - Calculate raw_sentiment_score                          │
│     - Calculate aggregate_sentiment_score (weighted)         │
│     - Calculate engagement_score                             │
│     - Calculate confidence                                   │
│     - Determine recommendation (BUY/HOLD/SELL)               │
│  4. Write sentiment.json                                     │
│                                                               │
│  Output piped to Node.js → WebSocket logs                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ sentiment.json created
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         CONVERSION SCRIPT (convert_to_coin_data.py)          │
│                                                               │
│  1. Read sentiment.json                                      │
│  2. For each token:                                          │
│     a. Call DexScreener API                                  │
│        GET /tokens/{token}?chain=solana                      │
│        → price, address, 24h change, logo                    │
│                                                               │
│     b. If no logo, call Jupiter API                          │
│        GET /tokens (search token list)                       │
│        → logo URL from IPFS                                  │
│                                                               │
│     c. If still no logo, call Moralis API                    │
│        GET /solana/token/{address}/metadata                  │
│        → name, symbol, logo, decimals                        │
│                                                               │
│     d. Build coin object with all data                       │
│        { id, name, symbol, address, price, logo,             │
│          raw_sentiment, aggregate_sentiment,                 │
│          engagement, confidence, recommendation,             │
│          latestPost: { title, content, comments } }          │
│                                                               │
│  3. Write to ../public/coin-data.json                        │
│  4. Print "🎉 PROCESSING COMPLETE - FRONTEND UPDATED!"       │
│                                                               │
│  All output → Node.js → WebSocket logs                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ coin-data.json updated
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               BACKEND COMPLETION BROADCAST                    │
│                                                               │
│  broadcast({                                                 │
│    type: 'coin_data_updated',                                │
│    coins: 12,                                                │
│    timestamp: '2025-11-16T04:20:00.000Z'                     │
│  })                                                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ WebSocket message
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FRONTEND RECEIVES UPDATE EVENT                   │
│                                                               │
│  1. ScraperService.handleUpdate()                            │
│     case 'coin_data_updated':                                │
│       window.dispatchEvent('coin-data-updated')              │
│                                                               │
│  2. DataService event listener                               │
│     window.addEventListener('coin-data-updated'):            │
│       this.loadCoinData()                                    │
│                                                               │
│  3. Fetch coin-data.json                                     │
│     GET /coin-data.json?ts=1731726000000                     │
│                                                               │
│  4. Parse & map to Coin model                                │
│     const coins = coinDataArray.map(...)                     │
│                                                               │
│  5. Update signal                                            │
│     this.coins.set(coins)                                    │
│                                                               │
│  6. Angular change detection triggers                        │
│     All components re-render with new data                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ UI updates
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER SEES UPDATED UI                       │
│                                                               │
│  ✅ 12 new coin cards appear                                 │
│  ✅ Prices, logos, sentiment scores shown                    │
│  ✅ BUY/HOLD/SELL recommendations displayed                  │
│  ✅ Sidebar updated with coin list                           │
│  ✅ Total balance recalculated                               │
│  ✅ Live logs show completion message                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎬 Complete User Journey

### **Scenario: User Discovers a Trending Memecoin**

**Step-by-Step Experience:**

1. **User opens http://localhost:4200**
   - Dashboard loads with any existing coin data
   - WebSocket connects (green indicator)
   - Scraper status: OFF

2. **User clicks "AI Web Scraper" toggle ON**
   - Toggle switches to ON
   - Button shows "ACTIVE" with pulsing green dot
   - Backend starts Python scraper

3. **Real-time logs start streaming** (bottom of page)
   ```
   [10:15:32] ✅ Connected to scraper backend
   [10:15:35] Scraper started successfully
   [10:15:36] 🚀 Starting 3 Parallel Memecoin Sentiment Scrapers...
   [10:15:37] 📋 Scraping: r/altcoin, r/CryptoMoonShots, r/pumpfun
   ```

4. **User watches live scraping progress**
   - Logs auto-scroll to show latest activity
   - Each subreddit shows progress independently
   - Post counts increment in real-time
   - Token names appear as identified

5. **After ~3 minutes, scraper auto-completes**
   - Logs show "✅ All scrapers completed!"
   - Toggle automatically switches to OFF
   - Processing begins

6. **Sentiment analysis runs**
   - User sees each token being analyzed
   - Sentiment scores calculated
   - Confidence levels determined

7. **API calls fetch metadata**
   - DexScreener API calls shown
   - Prices retrieved
   - Jupiter logo lookups
   - Each token's data logged

8. **Dashboard updates automatically**
   - "✅ Coin data updated (12 coins)" appears in logs
   - Dashboard refreshes without reload
   - 12 new coin cards appear in grid

9. **User explores coin details**
   - Clicks on "HEGE" coin card
   - Sees:
     - Price: $0.000014
     - 24h Change: +15.38%
     - Sentiment gauges: Hype 84%, Community 100%, Popularity 32%
     - Overall Confidence: 75% → BUY
   - Scrolls down to see latest Reddit post
   - Reads comments discussing the token

10. **User clicks "Refresh Prices"**
    - Console shows: `[Refresh] Starting price refresh for 12 coins...`
    - Each coin price updated from live APIs
    - Dashboard reflects new prices instantly

11. **User can click "Transaction History"** (placeholder)
    - Button does nothing yet (future feature)

---

## 🔬 Technical Deep Dive

### **Critical Implementation Details**

#### **1. Why Unbuffered Python Output?**

**Problem:**
```python
# Normal Python (stdout buffered)
print("Starting scraper...")  # ← Not sent immediately to Node.js
time.sleep(10)                # ← User sees nothing for 10 seconds
print("Complete!")            # ← Both messages arrive at once
```

**Solution:**
```bash
# Run with -u flag
python3 -u main.py

# AND set environment variable
PYTHONUNBUFFERED=1
```

```python
# AND use flush=True
print("Starting scraper...", flush=True)  # ← Sent immediately
```

**Result:** Real-time log streaming to frontend!

---

#### **2. WebSocket vs HTTP Polling**

**Why WebSocket?**

| Approach | Latency | Bandwidth | Complexity | Real-time |
|----------|---------|-----------|------------|-----------|
| **HTTP Polling** | High (1-5s) | Wasteful | Low | No |
| **Long Polling** | Medium (100-500ms) | Medium | Medium | Partial |
| **WebSocket** | Low (<50ms) | Efficient | Medium | Yes ✅ |

**WebSocket Benefits:**
- Full-duplex communication (bidirectional)
- Single persistent connection (no handshake overhead)
- Push-based (server sends when ready, not on client request)
- Low latency (messages arrive instantly)

---

#### **3. File Watcher Strategy**

**Why Chokidar over fs.watch?**

```javascript
// Native fs.watch (unreliable)
fs.watch('file.json', () => {
  // Fires multiple times per change
  // Doesn't work on all platforms
  // No debouncing
});

// Chokidar (production-ready)
chokidar.watch('file.json', {
  persistent: true,
  ignoreInitial: false,
  awaitWriteFinish: {
    stabilityThreshold: 100,  // Wait 100ms after last change
    pollInterval: 50
  }
});
```

**Benefits:**
- Cross-platform reliability
- Prevents duplicate events
- Waits for file write completion
- Handles large files gracefully

---

#### **4. RxJS Observables vs Angular Signals**

**Data Flow Evolution:**

**Version 1: Callbacks (Bad)**
```typescript
scraperService.onUpdate((data) => {
  this.coins = data;  // Manual change detection needed
  this.cdr.detectChanges();
});
```

**Version 2: RxJS Observables (Good)**
```typescript
scraperService.data$.subscribe(data => {
  this.coins = data;  // Async pipe handles change detection
});
```

**Version 3: Signals (Best)**
```typescript
coins = toSignal(scraperService.data$);  // Auto-updates, fine-grained
// Template: {{ coins().length }}
```

**Why Signals Win:**
- Automatic dependency tracking
- Fine-grained reactivity (only updates what changed)
- Synchronous reads (no async pipe needed)
- Better performance (fewer change detection cycles)

---

#### **5. Parallel Scraping Architecture**

**Why 3 Threads?**

```python
# Sequential (slow: 9 minutes)
scrape('r/altcoin')        # 3 min
scrape('r/CryptoMoonShots')# 3 min
scrape('r/pumpfun')        # 3 min
# Total: 9 minutes

# Parallel (fast: 3 minutes)
with ThreadPoolExecutor(max_workers=3):
    executor.submit(scrape, 'r/altcoin')
    executor.submit(scrape, 'r/CryptoMoonShots')
    executor.submit(scrape, 'r/pumpfun')
# Total: 3 minutes (3x speedup!)
```

**Thread Safety:**
```python
# Global lock for JSON file writes
_json_file_lock = threading.Lock()

def save_post(post):
    with _json_file_lock:
        # Only one thread writes at a time
        existing = read_json()
        existing.append(post)
        write_json(existing)
```

---

#### **6. Agent API Rate Limiting**

**Problem:** 3 threads × 25 posts = 75 concurrent API calls = 💥

**Solution: Global Semaphore**
```python
# Only 1 agent call at a time across ALL threads
_agent_semaphore = threading.Semaphore(1)

def identify_token_async(post):
    _agent_semaphore.acquire()  # Wait for turn
    try:
        token = agent_client.identify_token(post.text)
    finally:
        _agent_semaphore.release()  # Next thread can proceed
```

**Result:** API calls queue up, preventing rate limit errors

---

#### **7. Cache Busting Strategy**

**Problem:**
```typescript
// Browser caches coin-data.json
fetch('/coin-data.json')  
// Returns old cached data even after update! 🐛
```

**Solution:**
```typescript
// Add timestamp query param
const ts = Date.now();
fetch(`/coin-data.json?ts=${ts}`, { cache: 'no-store' })
// Forces fresh fetch every time ✅
```

---

#### **8. Error Handling Patterns**

**Backend Process Management:**
```javascript
// Handle scraper crashes
scraperProcess.on('error', (error) => {
  console.error('Scraper process error:', error);
  scraperRunning = false;
  broadcast({ type: 'scraper_error', message: error.message });
});

// Prevent zombie processes
process.on('SIGINT', () => {
  if (scraperProcess) scraperProcess.kill('SIGTERM');
  process.exit(0);
});
```

**Frontend Reconnection:**
```typescript
ws.onclose = (event) => {
  if (event.code !== 1000) {  // Not normal closure
    // Exponential backoff: 2s → 4s → 8s → 16s → 30s
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
  }
};
```

---

## 📈 Performance Optimization

### **Bottlenecks & Solutions**

| Bottleneck | Impact | Solution Implemented |
|------------|--------|---------------------|
| Python output buffering | 5-10s log delay | `-u` flag + `PYTHONUNBUFFERED=1` + `flush=True` |
| Sequential scraping | 9 min total time | Parallel threads (3x speedup) |
| Agent API rate limits | Scraper crashes | Global semaphore queue |
| Browser cache | Stale data shown | Timestamp query params |
| WebSocket reconnect storms | Backend overload | Exponential backoff |
| Large JSON parsing | UI freeze | Incremental file updates |
| Multiple file watches | High CPU | Single watcher, debounced |

---

## 🎓 Key Takeaways

### **What Makes This Architecture Special?**

1. **Multi-Language Integration**
   - Python for scraping (better browser automation)
   - Node.js for backend (async I/O, WebSocket support)
   - TypeScript for frontend (type safety, modern features)
   - Each language used where it excels

2. **Event-Driven Architecture**
   - File changes trigger broadcasts (no polling)
   - Process events trigger pipelines
   - Frontend reacts to backend events
   - Loosely coupled components

3. **Real-Time User Experience**
   - See logs as they happen (<50ms latency)
   - Dashboard updates without refresh
   - Live progress indication
   - Feels like a desktop app

4. **Automated Pipeline**
   - Scraping → Sentiment → Metadata → Frontend
   - No manual steps required
   - Error recovery at each stage
   - Complete in ~5 minutes

5. **Developer Experience**
   - Hot reload on both ends
   - Comprehensive logging
   - Easy to debug
   - Modular design (easy to extend)

---

## 🚀 Future Enhancements

### **Planned Features**

1. **AI Buyer/Seller Agents**
   - Integrate wallet (Phantom)
   - Execute trades based on recommendations
   - Track P&L in real-time

2. **Historical Data**
   - Database instead of JSON
   - Time-series sentiment tracking
   - Price history charts

3. **Multiple Platforms**
   - Twitter/X scraping
   - Discord sentiment
   - Telegram groups

4. **Advanced Analytics**
   - Machine learning models
   - Prediction algorithms
   - Whale wallet tracking

5. **Production Deploy**
   - Docker containers
   - Redis for scaling
   - PostgreSQL database
   - PM2 process manager
   - NGINX reverse proxy

---

## 📚 Conclusion

This project demonstrates a **modern, event-driven architecture** that combines:
- ✅ Real-time bidirectional communication (WebSocket)
- ✅ Multi-language integration (Python + Node.js + TypeScript)
- ✅ Reactive state management (RxJS + Signals)
- ✅ Automated data pipelines
- ✅ Production-ready error handling

**The complete flow from user click to dashboard update takes ~5 minutes but feels instant due to live feedback at every step.**

---

**End of Complete Workflow Guide**
*Created for helloCoin'ed Code Jam 2025 Project*
*Last Updated: November 16, 2025*

