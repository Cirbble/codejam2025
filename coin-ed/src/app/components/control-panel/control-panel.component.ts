import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { ConfirmationModalComponent } from '../confirmation-modal/confirmation-modal.component';

@Component({
  selector: 'app-control-panel',
  standalone: true,
  imports: [CommonModule, ConfirmationModalComponent],
  templateUrl: './control-panel.component.html',
  styleUrls: ['./control-panel.component.css']
})
export class ControlPanelComponent {
  dataService = inject(DataService);
  
  showBuyerConfirmation = false;
  showSellerConfirmation = false;

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

  onBuyerToggle(event: Event): void {
    event.preventDefault();
    
    // Only allow toggle if scraper is enabled
    if (this.dataService.agentControls().scraperEnabled) {
      const currentState = this.dataService.agentControls().buyerEnabled;
      
      // If turning ON, show confirmation
      if (!currentState) {
        this.showBuyerConfirmation = true;
      } else {
        // If turning OFF, just toggle
        this.dataService.toggleBuyer();
        console.log('Buyer toggled:', this.dataService.agentControls().buyerEnabled);
      }
    }
  }

  onBuyerConfirm(): void {
    this.showBuyerConfirmation = false;
    this.dataService.toggleBuyer();
    console.log('Buyer toggled:', this.dataService.agentControls().buyerEnabled);
  }

  onBuyerCancel(): void {
    this.showBuyerConfirmation = false;
  }

  onSellerToggle(event: Event): void {
    event.preventDefault();
    
    // Only allow toggle if scraper is enabled
    if (this.dataService.agentControls().scraperEnabled) {
      const currentState = this.dataService.agentControls().sellerEnabled;
      
      // If turning ON, show confirmation
      if (!currentState) {
        this.showSellerConfirmation = true;
      } else {
        // If turning OFF, just toggle
        this.dataService.toggleSeller();
        console.log('Seller toggled:', this.dataService.agentControls().sellerEnabled);
      }
    }
  }

  onSellerConfirm(): void {
    this.showSellerConfirmation = false;
    this.dataService.toggleSeller();
    console.log('Seller toggled:', this.dataService.agentControls().sellerEnabled);
  }

  onSellerCancel(): void {
    this.showSellerConfirmation = false;
  }
}

