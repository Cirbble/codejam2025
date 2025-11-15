import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { DataLoaderService } from '../../services/data-loader.service';
import { ControlPanelComponent } from '../control-panel/control-panel.component';
import { CoinCardComponent } from '../coin-card/coin-card.component';
import { PortfolioComponent } from '../portfolio/portfolio.component';
import { ChartComponent } from '../chart/chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    ControlPanelComponent,
    CoinCardComponent,
    PortfolioComponent,
    ChartComponent
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent {
  dataService = inject(DataService);
  dataLoader = inject(DataLoaderService);

  loadExampleData(): void {
    this.dataLoader.loadFromFile('/example-data.json');
  }
}

