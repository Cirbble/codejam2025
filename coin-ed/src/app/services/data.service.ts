import { Injectable, signal } from '@angular/core';
import { Coin, Portfolio, SentimentData, AgentControls, PortfolioCoin } from '../models/coin.model';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  // Signals for reactive state management
  coins = signal<Coin[]>([]);
  portfolio = signal<Portfolio>({ totalBalance: 0, coins: [] });
  sentimentData = signal<SentimentData[]>([]);
  agentControls = signal<AgentControls>({
    scraperEnabled: false,
    buyerEnabled: false,
    sellerEnabled: false
  });

  constructor() {
    // Initialize with mock data
    this.initializeMockData();
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
        chartData: item.chartData || coins[existingCoinIndex].chartData
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
        icon: item.icon || ''
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
   * Initialize with mock data for demonstration
   */
  private initializeMockData(): void {
    const mockCoins: Coin[] = [
      {
        id: 'bitcoin',
        name: 'Bitcoin',
        symbol: 'BTC',
        price: 52291,
        balance: 52291,
        feedback: 'Feedback',
        changePercentage: 0.25,
        chartData: this.generateMockChartData(),
        icon: '₿'
      },
      {
        id: 'litecoin',
        name: 'Litecoin',
        symbol: 'LTC',
        price: 8291,
        balance: 8291,
        feedback: 'Feedback',
        changePercentage: 0.15,
        chartData: this.generateMockChartData(),
        icon: 'Ł'
      },
      {
        id: 'ethereum',
        name: 'Ethereum',
        symbol: 'ETH',
        price: 28291,
        balance: 28291,
        feedback: 'Feedback',
        changePercentage: 0.25,
        chartData: this.generateMockChartData(),
        icon: 'Ξ'
      },
      {
        id: 'solana',
        name: 'Solana',
        symbol: 'SOL',
        price: 14291,
        balance: 14291,
        feedback: 'Feedback',
        changePercentage: -0.25,
        chartData: this.generateMockChartData(),
        icon: '◎'
      }
    ];

    this.coins.set(mockCoins);
    this.updatePortfolio();
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
}

