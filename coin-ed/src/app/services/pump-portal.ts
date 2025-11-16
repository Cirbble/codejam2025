import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';

export interface TokenInfo {
  mint: string;
  name: string;
  symbol: string;
  description: string;
  image_uri: string;
  metadata_uri: string;
  twitter?: string;
  telegram?: string;
  bonding_curve: string;
  associated_bonding_curve: string;
  creator: string;
  created_timestamp: number;
  raydium_pool?: string;
  complete: boolean;
  virtual_sol_reserves: number;
  virtual_token_reserves: number;
  total_supply: number;
  website?: string;
  show_name: boolean;
  king_of_the_hill_timestamp?: number;
  market_cap: number;
  reply_count: number;
  last_reply: number;
  nsfw: boolean;
  market_id?: string;
  inverted?: boolean;
  is_currently_live: boolean;
  username?: string;
  profile_image?: string;
  usd_market_cap: number;
}

export interface PriceData {
  price: number;
  timestamp: number;
  market_cap?: number;
  volume_24h?: number;
}

@Injectable({
  providedIn: 'root'
})
export class PumpPortalService {
  private http = inject(HttpClient);
  private readonly API_BASE = 'https://pumpportal.fun/api';

  /**
   * Get current token information including price
   * @param tokenAddress The token mint address
   */
  getTokenInfo(tokenAddress: string): Observable<TokenInfo | null> {
    return this.http.get<TokenInfo>(`${this.API_BASE}/data/account/${tokenAddress}`).pipe(
      catchError(error => {
        console.error('Error fetching token info:', error);
        return of(null);
      })
    );
  }

  /**
   * Get historical price data for a token
   * Note: PumpPortal may not have a direct historical endpoint, 
   * but we can use the trade history to calculate historical prices
   */
  getHistoricalPrices(tokenAddress: string): Observable<PriceData[]> {
    // PumpPortal doesn't have a direct historical price endpoint
    // We would need to use trade history or other data sources
    // For now, return empty array
    console.log('Historical price data not directly available from PumpPortal API');
    return of([]);
  }

  /**
   * Calculate current price from token reserves
   * Price = virtual_sol_reserves / virtual_token_reserves
   */
  calculatePrice(tokenInfo: TokenInfo): number {
    if (tokenInfo.virtual_token_reserves === 0) return 0;
    return tokenInfo.virtual_sol_reserves / tokenInfo.virtual_token_reserves;
  }

  /**
   * Get price in USD (requires SOL price)
   * @param tokenInfo Token information
   * @param solPriceUSD Current SOL price in USD
   */
  getPriceInUSD(tokenInfo: TokenInfo, solPriceUSD: number): number {
    const priceInSOL = this.calculatePrice(tokenInfo);
    return priceInSOL * solPriceUSD;
  }

  /**
   * Search for HEGE token
   * Note: You'll need the actual mint address for HEGE
   */
  searchToken(query: string): Observable<any> {
    // PumpPortal doesn't have a search endpoint in the public API
    // You would need the exact mint address
    console.log('Token search not available, need exact mint address');
    return of(null);
  }
}
