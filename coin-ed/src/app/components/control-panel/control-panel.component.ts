import { Component, inject, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { BuySellModalComponent, AgentType } from '../buy-sell-modal/buy-sell-modal.component';
import { NotificationComponent } from '../notification/notification.component';

@Component({
  selector: 'app-control-panel',
  standalone: true,
  imports: [CommonModule, BuySellModalComponent, NotificationComponent],
  templateUrl: './control-panel.component.html',
  styleUrls: ['./control-panel.component.css']
})
export class ControlPanelComponent {
  dataService = inject(DataService);
  modal = viewChild<BuySellModalComponent>('buySellModal');
  notificationComponent = viewChild<NotificationComponent>('notificationComponent');
  private buyIntervalId: any = null;

  onScraperToggle(): void {
    this.dataService.toggleScraper();
    console.log('Scraper toggled:', this.dataService.agentControls().scraperEnabled);

    // If scraper is turned off, also turn off buyer and seller
    if (!this.dataService.agentControls().scraperEnabled) {
      const controls = this.dataService.agentControls();
      if (controls.buyerEnabled || controls.sellerEnabled) {
        this.dataService.agentControls.set({
          scraperEnabled: false,
          buyerEnabled: false,
          sellerEnabled: false
        });
        console.log('Buyer and Seller disabled due to scraper being turned off');
      }
    }
  }

  onBuyerToggle(): void {
    // Only allow toggle if scraper is enabled
    if (this.dataService.agentControls().scraperEnabled) {
      const wasEnabled = this.dataService.agentControls().buyerEnabled;
      
      if (!wasEnabled) {
        // Toggling ON - show modal but don't enable yet
        setTimeout(() => {
          this.modal()?.open('buyer');
        }, 100);
      } else {
        // Toggling OFF - disable and stop buying
        this.dataService.toggleBuyer();
        if (this.buyIntervalId) {
          clearInterval(this.buyIntervalId);
          this.buyIntervalId = null;
        }
        console.log('Buyer disabled');
      }
    }
  }

  onSellerToggle(): void {
    // Only allow toggle if scraper is enabled
    if (this.dataService.agentControls().scraperEnabled) {
      const wasEnabled = this.dataService.agentControls().sellerEnabled;
      this.dataService.toggleSeller();
      
      // If toggling ON, show the modal
      if (!wasEnabled && this.dataService.agentControls().sellerEnabled) {
        setTimeout(() => {
          this.modal()?.open('seller');
        }, 100);
      }
      
      console.log('Seller toggled:', this.dataService.agentControls().sellerEnabled);
    }
  }

  onActionConfirmed(data: { agentType: AgentType; action: 'buy' | 'sell' }): void {
    console.log(`${data.agentType} confirmed action: ${data.action}`);
    
    if (data.agentType === 'buyer' && data.action === 'buy') {
      // Enable the buyer agent if not already enabled
      if (!this.dataService.agentControls().buyerEnabled) {
        this.dataService.toggleBuyer();
      }
      // Start the automated buy process
      this.startAutomatedBuying();
    } else if (data.agentType === 'seller' && data.action === 'sell') {
      // Enable the seller agent if not already enabled
      if (!this.dataService.agentControls().sellerEnabled) {
        this.dataService.toggleSeller();
      }
    }
  }
  
  onModalClosed(): void {
    // Modal was closed - this could be from cancel or after confirm
    console.log('Modal closed');
  }

  private startAutomatedBuying(): void {
    console.log('startAutomatedBuying called');
    // Clear any existing interval
    if (this.buyIntervalId) {
      clearInterval(this.buyIntervalId);
    }

    // Schedule random buy notifications
    const scheduleBuy = () => {
      // Random delay between 1-5 seconds
      const delay = Math.floor(Math.random() * 4000) + 1000;
      console.log(`Next buy scheduled in ${delay}ms`);
      
      setTimeout(() => {
        if (this.dataService.agentControls().buyerEnabled) {
          this.executeBuy();
          scheduleBuy(); // Schedule next buy
        }
      }, delay);
    };

    scheduleBuy();
  }

  private executeBuy(): void {
    console.log('executeBuy called');
    const buyCoins = this.dataService.getBuyRecommendedCoins();
    
    console.log('Buy coins available:', buyCoins.length);
    
    if (buyCoins.length === 0) {
      console.log('No coins with BUY recommendation available');
      return;
    }

    // Pick a random coin from buy recommendations
    const coin = buyCoins[Math.floor(Math.random() * buyCoins.length)];
    
    console.log('Selected coin:', coin);
    
    // Calculate amount based on confidence (1-10 dollars)
    const confidence = coin.confidence || 50;
    const amount = 1 + (confidence / 100) * 9; // 1-10 dollars based on confidence
    
    console.log('Amount to buy:', amount, 'Confidence:', confidence);
    
    // Mark coin as purchased
    this.dataService.markCoinAsPurchased(coin.id);
    
    // Show notification
    const notifComp = this.notificationComponent();
    console.log('Notification component:', notifComp);
    
    if (notifComp) {
      notifComp.showBuyNotification(coin.name, amount);
      console.log(`Notification shown for ${coin.name}`);
    } else {
      console.error('Notification component not found!');
    }
    
    console.log(`AI bought $${amount.toFixed(2)} worth of ${coin.name}`);
  }

  ngOnDestroy(): void {
    if (this.buyIntervalId) {
      clearInterval(this.buyIntervalId);
    }
  }
}
