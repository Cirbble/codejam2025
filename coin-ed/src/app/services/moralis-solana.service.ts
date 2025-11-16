import { Injectable } from '@angular/core';
import { MORALIS_CONFIG } from '../config/moralis.config';

/**
 * Moralis Solana API Service
 * Complete integration for Solana blockchain data via Moralis API
 *
 * SETUP:
 * The API key is stored in .env file at: coin-ed/scrapper_and_analysis/.env
 *
 * USAGE:
 * 1. For server-side (SSR): Use getServerConfig('moralisApiKey') from server.config.ts
 * 2. For client-side: Create an API endpoint that proxies requests using the server-side key
 * 3. Or inject the key during component initialization: service.setApiKey(key)
 *
 * EXAMPLE:
 * ```typescript
 * const moralis = inject(MoralisSolanaService);
 *
 * // Set API key (get from backend endpoint or SSR injection)
 * moralis.setApiKey('your_api_key_from_backend');
 *
 * // Use the service
 * const data = await moralis.getFullTokenData(address);
 * ```
 */

export interface TokenMetadata {
  address: string;
  name: string;
  symbol: string;
  logo?: string;
  decimals: number;
  supply?: number;
  metadata?: any;
}

export interface TokenPrice {
  priceUSD: number;
  priceChange24h?: number;
  liquidity?: number;
  volume24h?: number;
}

export interface TokenPair {
  pairAddress: string;
  baseToken: string;
  quoteToken: string;
  liquidity: number;
  volume24h: number;
}

export interface PairStats {
  pairAddress: string;
  priceUSD: number;
  liquidity: number;
  volume24h: number;
  priceChange24h: number;
}

export interface TokenHolder {
  address: string;
  balance: number;
  percentage: number;
}

export interface FullTokenData {
  name: string;
  symbol: string;
  logo_url?: string;
  price: number;
  priceChange24h?: number;
  liquidity?: number;
  volume?: number;
  supply?: number;
  holders?: TokenHolder[];
  pairs?: TokenPair[];
  metadata?: any;
  address: string;
  decimals: number;
}

@Injectable({
  providedIn: 'root'
})
export class MoralisSolanaService {
  private apiKey: string = '';
  private maxRetries = 3;
  private retryDelay = 1000; // ms

  constructor() {
    // API key must be set explicitly via setApiKey()
    // This is because Angular frontend can't directly access .env files
    // The key should be loaded from:
    // 1. Backend API endpoint
    // 2. SSR injection
    // 3. Configuration service
  }

  /**
   * Set API key programmatically
   */
  setApiKey(key: string): void {
    this.apiKey = key;
  }

  /**
   * Validate Solana address format
   */
  private validateAddress(address: string): boolean {
    // Solana addresses are base58 encoded, typically 32-44 characters
    const solanaAddressRegex = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
    return solanaAddressRegex.test(address);
  }

  /**
   * Generic fetch with retry logic
   */
  private async fetchWithRetry(url: string, options: RequestInit = {}, retries = this.maxRetries): Promise<any> {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Accept': 'application/json',
          'X-API-Key': this.apiKey,
          ...options.headers
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (retries > 0) {
        console.warn(`Request failed, retrying... (${retries} attempts left)`);
        await new Promise(resolve => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(url, options, retries - 1);
      }
      throw error;
    }
  }

  /**
   * Get token metadata
   * GET https://solana-gateway.moralis.io/token/mainnet/:address/metadata
   */
  async getTokenMetadata(address: string): Promise<TokenMetadata | null> {
    if (!this.validateAddress(address)) {
      console.error('Invalid Solana address:', address);
      return null;
    }

    try {
      const url = `${MORALIS_CONFIG.SOLANA_GATEWAY}/token/mainnet/${address}/metadata`;
      const data = await this.fetchWithRetry(url);

      return {
        address: data.mint || address,
        name: data.name || 'Unknown',
        symbol: data.symbol || '???',
        logo: data.logoURI || data.logo,
        decimals: data.decimals || 9,
        supply: data.supply,
        metadata: data
      };
    } catch (error) {
      console.error('Error fetching token metadata:', error);
      return null;
    }
  }

  /**
   * Get token price
   * GET https://solana-gateway.moralis.io/token/mainnet/:address/price
   */
  async getTokenPrice(address: string): Promise<TokenPrice | null> {
    if (!this.validateAddress(address)) {
      console.error('Invalid Solana address:', address);
      return null;
    }

    try {
      const url = `${MORALIS_CONFIG.SOLANA_GATEWAY}/token/mainnet/${address}/price`;
      const data = await this.fetchWithRetry(url);

      return {
        priceUSD: data.usdPrice || 0,
        priceChange24h: data['24hrPercentChange'],
        liquidity: data.liquidity?.usd,
        volume24h: data.volume24h
      };
    } catch (error) {
      console.error('Error fetching token price:', error);
      return null;
    }
  }

  /**
   * Get trending tokens
   * GET https://deep-index.moralis.io/api/v2.2/tokens/trending
   */
  async getTrendingTokens(): Promise<any[]> {
    try {
      const url = `${MORALIS_CONFIG.DEEP_INDEX}/tokens/trending`;
      const data = await this.fetchWithRetry(url);
      return data.tokens || [];
    } catch (error) {
      console.error('Error fetching trending tokens:', error);
      return [];
    }
  }

  /**
   * Get token pairs
   * GET https://solana-gateway.moralis.io/token/mainnet/:address/pairs
   */
  async getTokenPairs(address: string): Promise<TokenPair[]> {
    if (!this.validateAddress(address)) {
      console.error('Invalid Solana address:', address);
      return [];
    }

    try {
      const url = `${MORALIS_CONFIG.SOLANA_GATEWAY}/token/mainnet/${address}/pairs`;
      const data = await this.fetchWithRetry(url);

      if (!data.pairs) return [];

      return data.pairs.map((pair: any) => ({
        pairAddress: pair.pairAddress,
        baseToken: pair.baseToken,
        quoteToken: pair.quoteToken,
        liquidity: pair.liquidity?.usd || 0,
        volume24h: pair.volume24h || 0
      }));
    } catch (error) {
      console.error('Error fetching token pairs:', error);
      return [];
    }
  }

  /**
   * Get pair statistics
   * GET https://solana-gateway.moralis.io/token/mainnet/pairs/:pairAddress/stats
   */
  async getPairStats(pairAddress: string): Promise<PairStats | null> {
    if (!this.validateAddress(pairAddress)) {
      console.error('Invalid Solana pair address:', pairAddress);
      return null;
    }

    try {
      const url = `${MORALIS_CONFIG.SOLANA_GATEWAY}/token/mainnet/pairs/${pairAddress}/stats`;
      const data = await this.fetchWithRetry(url);

      return {
        pairAddress,
        priceUSD: data.priceUsd || 0,
        liquidity: data.liquidity?.usd || 0,
        volume24h: data.volume24h || 0,
        priceChange24h: data.priceChange24h || 0
      };
    } catch (error) {
      console.error('Error fetching pair stats:', error);
      return null;
    }
  }

  /**
   * Get token holders
   * GET https://solana-gateway.moralis.io/token/mainnet/holders/:address
   */
  async getTokenHolders(address: string): Promise<TokenHolder[]> {
    if (!this.validateAddress(address)) {
      console.error('Invalid Solana address:', address);
      return [];
    }

    try {
      const url = `${MORALIS_CONFIG.SOLANA_GATEWAY}/token/mainnet/holders/${address}`;
      const data = await this.fetchWithRetry(url);

      if (!data.holders) return [];

      return data.holders.map((holder: any) => ({
        address: holder.address,
        balance: holder.balance,
        percentage: holder.percentage || 0
      }));
    } catch (error) {
      console.error('Error fetching token holders:', error);
      return [];
    }
  }

  /**
   * Master function: Get complete token data
   * Combines all API calls into a single comprehensive object
   */
  async getFullTokenData(address: string): Promise<FullTokenData | null> {
    if (!this.validateAddress(address)) {
      console.error('Invalid Solana address:', address);
      return null;
    }

    console.log(`Fetching full token data for: ${address}`);

    try {
      // Fetch all data in parallel for efficiency
      const [metadata, price, pairs, holders] = await Promise.allSettled([
        this.getTokenMetadata(address),
        this.getTokenPrice(address),
        this.getTokenPairs(address),
        this.getTokenHolders(address)
      ]);

      const tokenMetadata = metadata.status === 'fulfilled' ? metadata.value : null;
      const tokenPrice = price.status === 'fulfilled' ? price.value : null;
      const tokenPairs = pairs.status === 'fulfilled' ? pairs.value : [];
      const tokenHolders = holders.status === 'fulfilled' ? holders.value : [];

      if (!tokenMetadata) {
        console.error('Failed to fetch token metadata');
        return null;
      }

      return {
        name: tokenMetadata.name,
        symbol: tokenMetadata.symbol,
        logo_url: tokenMetadata.logo,
        price: tokenPrice?.priceUSD || 0,
        priceChange24h: tokenPrice?.priceChange24h,
        liquidity: tokenPrice?.liquidity,
        volume: tokenPrice?.volume24h,
        supply: tokenMetadata.supply,
        holders: tokenHolders,
        pairs: tokenPairs,
        metadata: tokenMetadata.metadata,
        address: address,
        decimals: tokenMetadata.decimals
      };
    } catch (error) {
      console.error('Error fetching full token data:', error);
      return null;
    }
  }

  /**
   * Batch fetch multiple tokens
   */
  async getMultipleTokensData(addresses: string[]): Promise<FullTokenData[]> {
    const validAddresses = addresses.filter(addr => this.validateAddress(addr));

    if (validAddresses.length === 0) {
      console.warn('No valid addresses provided');
      return [];
    }

    const results = await Promise.allSettled(
      validAddresses.map(addr => this.getFullTokenData(addr))
    );

    return results
      .filter((result): result is PromiseFulfilledResult<FullTokenData | null> =>
        result.status === 'fulfilled' && result.value !== null)
      .map(result => result.value!);
  }
}

// Example usage (commented out for production)
/*
// To test this service:
const service = new MoralisSolanaService();
service.setApiKey('YOUR_MORALIS_API_KEY');

// Example: Get full data for a Solana token
const tokenAddress = 'So11111111111111111111111111111111111111112'; // SOL
service.getFullTokenData(tokenAddress).then(data => {
  console.log('Full Token Data:', data);
});

// Example: Get multiple tokens
const addresses = [
  'So11111111111111111111111111111111111111112', // SOL
  'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'  // USDC
];
service.getMultipleTokensData(addresses).then(tokens => {
  console.log('Multiple Tokens:', tokens);
});
*/

