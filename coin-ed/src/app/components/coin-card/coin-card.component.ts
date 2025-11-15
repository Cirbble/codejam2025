import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Coin } from '../../models/coin.model';
import { GaugeComponent } from '../gauge/gauge';

@Component({
  selector: 'app-coin-card',
  standalone: true,
  imports: [CommonModule, GaugeComponent],
  templateUrl: './coin-card.component.html',
  styleUrls: ['./coin-card.component.css']
})
export class CoinCardComponent {
  @Input() coin!: Coin;

  generateChartPoints(): string {
    if (!this.coin.chartData || this.coin.chartData.length === 0) {
      return '';
    }

    const data = this.coin.chartData;
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min;

    return data
      .map((value, index) => {
        const x = (index / (data.length - 1)) * 200;
        const y = 60 - ((value - min) / range) * 60;
        return `${x},${y}`;
      })
      .join(' ');
  }

  calculateConfidence(): number {
    if (!this.coin.hype && !this.coin.communityHype && !this.coin.popularity) {
      return 0;
    }
    const hype = this.coin.hype || 0;
    const community = this.coin.communityHype || 0;
    const popularity = this.coin.popularity || 0;
    
    // Weighted average: 30% hype, 40% community, 30% popularity
    return (hype * 0.3 + community * 0.4 + popularity * 0.3);
  }

  getConfidenceColor(): string {
    const confidence = this.calculateConfidence();
    if (confidence >= 0.7) return '#00d4aa'; // Green
    if (confidence >= 0.4) return '#6B8AFF'; // Blue
    return '#ff6b6b'; // Red
  }
}

