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
  }

  onBuyerToggle(): void {
    this.dataService.toggleBuyer();
    console.log('Buyer toggled:', this.dataService.agentControls().buyerEnabled);
  }

  onSellerToggle(): void {
    this.dataService.toggleSeller();
    console.log('Seller toggled:', this.dataService.agentControls().sellerEnabled);
  }
}

