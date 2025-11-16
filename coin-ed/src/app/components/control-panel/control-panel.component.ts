import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';

@Component({
  selector: 'app-control-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './control-panel.component.html',
  styleUrls: ['./control-panel.component.css']
})
export class ControlPanelComponent {
  dataService = inject(DataService);

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
      this.dataService.toggleBuyer();
      console.log('Buyer toggled:', this.dataService.agentControls().buyerEnabled);
    }
  }

  onSellerToggle(): void {
    // Only allow toggle if scraper is enabled
    if (this.dataService.agentControls().scraperEnabled) {
      this.dataService.toggleSeller();
      console.log('Seller toggled:', this.dataService.agentControls().sellerEnabled);
    }
  }
}

