export interface Coin {
  id: string;
  name: string;
  symbol: string;
  address?: string; // Blockchain address
  price: number;
  balance: number;
  decimals?: number; // Token decimals
  logo?: string; // Logo URL from API
  chain?: string; // Blockchain (solana, ethereum, etc)
  feedback: string;
  changePercentage: number;
  chartData?: number[];
  icon?: string;
  hype?: number; // raw_sentiment_score
  communityHype?: number; // aggregate_sentiment_score
  popularity?: number; // engagement_score
  confidence?: number; // calculated from the three scores
  recommendation?: string; // BUY/HOLD/SELL
  latestPost?: CoinPost;
}

export interface CoinPost {
  id: number;
  source: string;
  platform: string;
  title: string;
  content: string;
  author: string;
  timestamp: string;
  post_age: string;
  upvotes_likes: number;
  comment_count: number;
  comments: string[];
  link: string;
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

