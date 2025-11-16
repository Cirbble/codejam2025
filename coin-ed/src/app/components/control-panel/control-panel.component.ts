import { Component, inject, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { BuySellModalComponent, AgentType } from '../buy-sell-modal/buy-sell-modal.component';

@Component({
  selector: 'app-control-panel',
  standalone: true,
  imports: [CommonModule, BuySellModalComponent],
  templateUrl: './control-panel.component.html',
  styleUrls: ['./control-panel.component.css']
})
export class ControlPanelComponent {
  dataService = inject(DataService);
  modal = viewChild<BuySellModalComponent>('buySellModal');

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
      this.dataService.toggleBuyer();
      
      // If toggling ON, show the modal
      if (!wasEnabled && this.dataService.agentControls().buyerEnabled) {
        setTimeout(() => {
          this.modal()?.open('buyer');
        }, 100);
      }
      
      console.log('Buyer toggled:', this.dataService.agentControls().buyerEnabled);
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

  onActionSelected(data: { agentType: AgentType; action: 'buy' | 'sell' }): void {
    console.log(`${data.agentType} selected action: ${data.action}`);
    // Here you can add additional logic like saving the action, making API calls, etc.
  }
}

