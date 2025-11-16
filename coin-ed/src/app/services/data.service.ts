import { Injectable, signal, inject } from '@angular/core';
import { Coin, Portfolio, SentimentData, AgentControls, PortfolioCoin } from '../models/coin.model';
import { PumpPortalService } from './pump-portal';
import { getTokenAddress } from '../config/token-addresses';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private pumpPortal = inject(PumpPortalService);

  // Signals for reactive state management
  coins = signal<Coin[]>([]);
  portfolio = signal<Portfolio>({ totalBalance: 0, coins: [] });
  sentimentData = signal<SentimentData[]>([]);
  agentControls = signal<AgentControls>({
    scraperEnabled: false,
    buyerEnabled: false,
    sellerEnabled: false
  });
  
  // Track purchased coins to prevent duplicate buys
  private purchasedCoins = new Set<string>();

  constructor() {
    // Load data from coin-data.json
    this.loadCoinData();
  }

  /**
   * Parse incoming JSON data from scrapers/agents
   * This will either create new coin tabs or update existing ones
   */
  parseScrapedData(jsonData: any): void {
    try {
      if (Array.isArray(jsonData)) {
        jsonData.forEach(item => this.processDataItem(item));
      } else {
        this.processDataItem(jsonData);
      }
      this.updatePortfolio();
    } catch (error) {
      console.error('Error parsing scraped data:', error);
    }
  }

  /**
   * Process individual data item from JSON
   */
  private processDataItem(item: any): void {
    const coinId = item.coinId || item.id || item.symbol;
    const existingCoinIndex = this.coins().findIndex(c => c.id === coinId);

    if (existingCoinIndex >= 0) {
      // Update existing coin
      const coins = [...this.coins()];
      coins[existingCoinIndex] = {
        ...coins[existingCoinIndex],
        price: item.price || coins[existingCoinIndex].price,
        changePercentage: item.changePercentage || coins[existingCoinIndex].changePercentage,
        feedback: item.feedback || coins[existingCoinIndex].feedback,
        chartData: item.chartData || coins[existingCoinIndex].chartData,
        hype: item.raw_sentiment_score !== undefined ? item.raw_sentiment_score : coins[existingCoinIndex].hype,
        communityHype: item.aggregate_sentiment_score !== undefined ? item.aggregate_sentiment_score : coins[existingCoinIndex].communityHype,
        popularity: item.engagement_score !== undefined ? item.engagement_score : coins[existingCoinIndex].popularity,
        latestPost: this.extractPostData(item) || coins[existingCoinIndex].latestPost
      };
      this.coins.set(coins);
    } else {
      // Create new coin tab
      const newCoin: Coin = {
        id: coinId,
        name: item.name || coinId,
        symbol: item.symbol || coinId,
        price: item.price || 0,
        balance: item.balance || 0,
        feedback: item.feedback || '',
        changePercentage: item.changePercentage || 0,
        chartData: item.chartData || [],
        icon: item.icon || '',
        hype: item.raw_sentiment_score,
        communityHype: item.aggregate_sentiment_score,
        popularity: item.engagement_score,
        latestPost: this.extractPostData(item)
      };
      this.coins.set([...this.coins(), newCoin]);
    }

    // Update sentiment data if provided
    if (item.sentiment) {
      this.updateSentimentData(item);
    }
  }

  /**
   * Update sentiment data for a coin
   */
  private updateSentimentData(item: any): void {
    const sentimentEntry: SentimentData = {
      coinId: item.coinId || item.id,
      coinName: item.name,
      sentiment: item.sentiment.type || 'neutral',
      score: item.sentiment.score || 0,
      sources: item.sentiment.sources || [],
      timestamp: new Date()
    };

    const existingIndex = this.sentimentData().findIndex(s => s.coinId === sentimentEntry.coinId);
    if (existingIndex >= 0) {
      const data = [...this.sentimentData()];
      data[existingIndex] = sentimentEntry;
      this.sentimentData.set(data);
    } else {
      this.sentimentData.set([...this.sentimentData(), sentimentEntry]);
    }
  }

  /**
   * Update portfolio calculation
   */
  private updatePortfolio(): void {
    const coins = this.coins();
    const totalBalance = coins.reduce((sum, coin) => sum + coin.balance, 0);

    const portfolioCoins: PortfolioCoin[] = coins
      .filter(coin => coin.balance > 0)
      .map(coin => ({
        name: coin.name,
        symbol: coin.symbol,
        percentage: totalBalance > 0 ? Math.round((coin.balance / totalBalance) * 100) : 0,
        icon: coin.icon
      }))
      .sort((a, b) => b.percentage - a.percentage);

    this.portfolio.set({ totalBalance, coins: portfolioCoins });
  }

  /**
   * Toggle agent controls
   */
  toggleScraper(): void {
    const current = this.agentControls();
    this.agentControls.set({ ...current, scraperEnabled: !current.scraperEnabled });
  }

  toggleBuyer(): void {
    const current = this.agentControls();
    this.agentControls.set({ ...current, buyerEnabled: !current.buyerEnabled });
  }

  toggleSeller(): void {
    const current = this.agentControls();
    this.agentControls.set({ ...current, sellerEnabled: !current.sellerEnabled });
  }

  /**
   * Load coin data from coin-data.json file
   */
  private async loadCoinData(): Promise<void> {
    try {
      const response = await fetch('/coin-data.json');
      const coinDataArray = await response.json();
      
      const coins: any[] = coinDataArray.map((item: any) => ({
        id: item.id,
        name: item.name,
        symbol: item.symbol,
        price: item.price,
        balance: item.balance,
        feedback: item.feedback,
        changePercentage: item.changePercentage,
        chartData: this.generateMockChartData(),
        icon: item.icon,
        hype: item.raw_sentiment_score,
        communityHype: item.aggregate_sentiment_score,
        popularity: item.engagement_score,
        latestPost: this.extractPostData(item),
        // Include additional fields from coin-data.json
        recommendation: item.recommendation,
        confidence: item.confidence
      }));

      this.coins.set(coins);
      this.updatePortfolio();
      console.log('Loaded coins with recommendations:', coins.filter(c => c.recommendation === 'BUY').length);
    } catch (error) {
      console.error('Error loading coin data:', error);
      // Fallback to empty array if file can't be loaded
      this.coins.set([]);
    }
  }

  /**
   * Generate mock chart data
   */
  private generateMockChartData(): number[] {
    const data: number[] = [];
    let base = 30000 + Math.random() * 20000;
    for (let i = 0; i < 50; i++) {
      base += (Math.random() - 0.5) * 3000;
      data.push(base);
    }
    return data;
  }

  /**
   * Extract post data from scraped item
   */
  private extractPostData(item: any): any {
    // Check if item has post-like structure from sentiment.json
    if (item.title && item.source && item.platform) {
      const postData = {
        id: item.id,
        source: item.source,
        platform: item.platform,
        title: item.title,
        content: item.content || '',
        author: item.author,
        timestamp: item.timestamp,
        post_age: item.post_age,
        upvotes_likes: item.upvotes_likes || 0,
        comment_count: item.comment_count || 0,
        comments: Array.isArray(item.comments) ? item.comments : [],
        link: item.link || ''
      };
      console.log('Extracted post data:', postData);
      console.log('Comments count:', postData.comments.length);
      return postData;
    }
    return undefined;
  }

  /**
   * Fetch real-time price from PumpPortal for a coin
   */
  fetchPumpPortalPrice(coinSymbol: string): void {
    const tokenAddress = getTokenAddress(coinSymbol);
    
    if (!tokenAddress) {
      console.log(`No token address configured for ${coinSymbol}`);
      return;
    }

    console.log(`Fetching price for ${coinSymbol} from PumpPortal...`);
    
    this.pumpPortal.getTokenInfo(tokenAddress).subscribe(tokenInfo => {
      if (tokenInfo) {
        const priceInSOL = this.pumpPortal.calculatePrice(tokenInfo);
        const priceInUSD = tokenInfo.usd_market_cap / tokenInfo.total_supply;
        
        console.log(`${coinSymbol} Price:`, {
          priceInSOL,
          priceInUSD,
          marketCap: tokenInfo.usd_market_cap,
          totalSupply: tokenInfo.total_supply
        });

        // Update the coin with real price data
        const coins = this.coins();
        const coinIndex = coins.findIndex(c => c.symbol === coinSymbol);
        
        if (coinIndex >= 0) {
          const updatedCoins = [...coins];
          updatedCoins[coinIndex] = {
            ...updatedCoins[coinIndex],
            price: priceInUSD,
            balance: priceInUSD // Update balance to match price for now
          };
          this.coins.set(updatedCoins);
          this.updatePortfolio();
        }
      } else {
        console.log(`Could not fetch price for ${coinSymbol}`);
      }
    });
  }

  /**
   * Fetch prices for all coins that have token addresses configured
   */
  fetchAllPumpPortalPrices(): void {
    const coins = this.coins();
    coins.forEach(coin => {
      this.fetchPumpPortalPrice(coin.symbol);
    });
  }

  /**
   * Get coins with BUY recommendation that haven't been purchased yet
   */
  getBuyRecommendedCoins(): any[] {
    const allCoins = this.coins();
    console.log('All coins:', allCoins.length);
    console.log('Sample coin:', allCoins[0]);
    
    const buyCoins = allCoins.filter(coin => {
      const coinData = coin as any;
      const hasBuyRec = coinData.recommendation === 'BUY';
      const notPurchased = !this.purchasedCoins.has(coin.id);
      console.log(`Coin ${coin.name}: recommendation=${coinData.recommendation}, purchased=${!notPurchased}`);
      return hasBuyRec && notPurchased;
    });
    
    console.log('Buy recommended coins:', buyCoins.length);
    return buyCoins;
  }

  /**
   * Mark a coin as purchased to prevent duplicate buys
   */
  markCoinAsPurchased(coinId: string): void {
    this.purchasedCoins.add(coinId);
  }

  /**
   * Reset purchased coins (useful when restarting the agent)
   */
  resetPurchasedCoins(): void {
    this.purchasedCoins.clear();
  }
}

