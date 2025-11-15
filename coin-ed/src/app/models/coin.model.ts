export interface Coin {
  id: string;
  name: string;
  symbol: string;
  price: number;
  balance: number;
  feedback: string;
  changePercentage: number;
  chartData?: number[];
  icon?: string;
}

export interface Portfolio {
  totalBalance: number;
  coins: PortfolioCoin[];
}

export interface PortfolioCoin {
  name: string;
  symbol: string;
  percentage: number;
  icon?: string;
}

export interface ChartData {
  labels: string[];
  prices: number[];
  volumes: number[];
}

export interface SentimentData {
  coinId: string;
  coinName: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  sources: SentimentSource[];
  timestamp: Date;
}

export interface SentimentSource {
  platform: 'reddit' | 'twitter' | 'other';
  url: string;
  text: string;
  sentiment: number;
}

export interface AgentControls {
  scraperEnabled: boolean;
  buyerEnabled: boolean;
  sellerEnabled: boolean;
}

