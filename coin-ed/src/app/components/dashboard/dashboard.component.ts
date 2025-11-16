import { Component, inject, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DataService } from '../../services/data.service';
import { DataLoaderService } from '../../services/data-loader.service';
import { ControlPanelComponent } from '../control-panel/control-panel.component';
import { CoinCardComponent } from '../coin-card/coin-card.component';
import { PostDisplayComponent } from '../post-display/post-display';
import { ScraperLogsComponent } from '../scraper-logs/scraper-logs.component';
import { NotificationComponent } from '../notification/notification.component';
import { TransactionHistoryComponent } from '../transaction-history/transaction-history.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ControlPanelComponent,
    CoinCardComponent,
    PostDisplayComponent,
    ScraperLogsComponent,
    NotificationComponent,
    TransactionHistoryComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements AfterViewInit {
  private router = inject(Router);
  dataService = inject(DataService);
  dataLoader = inject(DataLoaderService);

  @ViewChild(NotificationComponent) notificationComponent!: NotificationComponent;

  selectedCoinId: string | null = null;
  recentlyUpdatedCoins: Set<string> = new Set();
  showTransactionHistory = false;

  ngAfterViewInit(): void {
    // Connect the notification component to the data service
    this.dataService.onBuyNotification = (message: string) => {
      if (this.notificationComponent) {
        this.notificationComponent.addNotification(message, 'buy');
      }
    };

    // Handle insufficient funds notification
    this.dataService.onInsufficientFunds = () => {
      if (this.notificationComponent) {
        this.notificationComponent.addNotification(
          'AI Buyer stopped due to insufficient funds. Please add more balance in settings.',
          'sell',
          'Insufficient Funds'
        );
      }
    };

    // Expose transaction methods to console for debugging
    if (typeof window !== 'undefined') {
      (window as any).viewTransactions = () => {
        const transactions = this.dataService.getTransactions();
        console.table(transactions.map(t => ({
          Time: t.timestamp.toLocaleString(),
          Type: t.type.toUpperCase(),
          Coin: `${t.coinName} (${t.coinSymbol})`,
          Amount: `$${t.amount}.00`,
          Confidence: `${t.confidence}%`
        })));
        console.log(`Total Buy Amount: $${this.dataService.getTotalBuyAmount()}.00`);
        console.log(`Total Sell Amount: $${this.dataService.getTotalSellAmount()}.00`);
        return transactions;
      };
      (window as any).clearTransactions = () => {
        this.dataService.clearTransactions();
        console.log('All transactions cleared');
      };
      console.log('💡 Transaction helpers available:');
      console.log('  - viewTransactions() - View all transactions');
      console.log('  - clearTransactions() - Clear transaction history');
    }
  }

  openTransactionHistory(): void {
    this.showTransactionHistory = true;
  }

  closeTransactionHistory(): void {
    this.showTransactionHistory = false;
  }

  refreshPrices(): void {
    console.log('Fetching prices from PumpPortal...');
    this.dataService.fetchAllPumpPortalPrices();
  }

  getSortedCoins() {
    const coins = [...this.dataService.coins()];
    // Sort by recently updated first, then by name
    return coins.sort((a, b) => {
      const aRecent = this.recentlyUpdatedCoins.has(a.id);
      const bRecent = this.recentlyUpdatedCoins.has(b.id);
      if (aRecent && !bRecent) return -1;
      if (!aRecent && bRecent) return 1;
      return a.name.localeCompare(b.name);
    });
  }

  selectCoin(coinId: string): void {
    this.selectedCoinId = this.selectedCoinId === coinId ? null : coinId;
  }

  getSelectedCoin() {
    if (!this.selectedCoinId) return null;
    return this.dataService.coins().find(c => c.id === this.selectedCoinId);
  }

  isRecentlyUpdated(coinId: string): boolean {
    return this.recentlyUpdatedCoins.has(coinId);
  }

  /**
   * Calculate overall confidence score from sentiment metrics with inverse bell curve
   * Returns a percentage (0-100) with U-shaped distribution (more extremes, less middle)
   */
  getConfidenceScore(coin: any): number {
    // Combine hype (raw sentiment), communityHype (aggregate), and popularity (engagement)
    // Weight: 30% raw sentiment, 50% aggregate sentiment, 20% engagement
    const hype = coin.hype || 0.5;  // Default to neutral
    const communityHype = coin.communityHype || 0.5;
    const popularity = coin.popularity || 0.5;

    // All values already in 0-1 range
    // Calculate weighted average
    let confidence = (hype * 0.3) + (communityHype * 0.5) + (popularity * 0.2);

    // Apply inverse bell curve transformation (U-shape)
    // This pushes values away from 0.5 (middle) toward 0 or 1 (extremes)
    const center = 0.5;
    const distanceFromCenter = Math.abs(confidence - center);

    // Amplify distance from center using power function
    // Values near 0.5 get pushed toward extremes
    const amplifiedDistance = Math.pow(distanceFromCenter * 2, 1.4) / 2;

    if (confidence < center) {
      // Push down toward 0
      confidence = center - amplifiedDistance;
    } else {
      // Push up toward 1
      confidence = center + amplifiedDistance;
    }

    // Ensure bounds
    confidence = Math.max(0, Math.min(1, confidence));

    // Convert to percentage
    return Math.round(confidence * 100);
  }

  openSettings(): void {
    this.router.navigate(['/settings']);
  }

  goToHomepage(): void {
    this.selectedCoinId = null;
  }

  /**
   * Get recommendation (BUY/HOLD/SELL) based on confidence score
   */
  getRecommendation(coin: any): string {
    // If coin already has recommendation from backend, use it
    if (coin.recommendation) {
      return coin.recommendation;
    }

    // Otherwise calculate it
    const confidence = this.getConfidenceScore(coin);
    if (confidence >= 75) return 'BUY';
    if (confidence >= 55) return 'HOLD';
    return 'SELL';
  }

  /**
   * Handle sidebar logo image errors
   */
  onSidebarImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
    const parent = img.parentElement;
    if (parent) {
      const fallback = document.createElement('span');
      fallback.className = 'sidebar-coin-text';
      fallback.textContent = img.alt.charAt(0);
      parent.appendChild(fallback);
    }
  }
}

