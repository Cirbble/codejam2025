import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { DataService } from '../../services/data.service';
import { DataLoaderService } from '../../services/data-loader.service';
import { ControlPanelComponent } from '../control-panel/control-panel.component';
import { CoinCardComponent } from '../coin-card/coin-card.component';
import { PortfolioComponent } from '../portfolio/portfolio.component';
import { ChartComponent } from '../chart/chart.component';
import { PostDisplayComponent } from '../post-display/post-display';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ControlPanelComponent,
    CoinCardComponent,
    PortfolioComponent,
    ChartComponent,
    PostDisplayComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  private router = inject(Router);
  dataService = inject(DataService);
  dataLoader = inject(DataLoaderService);

  selectedCoinId: string | null = null;
  recentlyUpdatedCoins: Set<string> = new Set();

  loadExampleData(): void {
    this.dataLoader.loadFromFile('/coin-data.json');
    // Mark newly loaded coins as recently updated
    setTimeout(() => {
      const coins = this.dataService.coins();
      coins.forEach(coin => {
        if (!this.recentlyUpdatedCoins.has(coin.id)) {
          this.recentlyUpdatedCoins.add(coin.id);
        }
      });
      // Clear "new" badges after 5 seconds
      setTimeout(() => {
        this.recentlyUpdatedCoins.clear();
      }, 5000);
    }, 100);
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

  openSettings(): void {
    this.router.navigate(['/settings']);
  }
}

