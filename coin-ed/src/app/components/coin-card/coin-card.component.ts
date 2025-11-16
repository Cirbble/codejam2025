import { Component, Input, Output, EventEmitter } from '@angular/core';
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
  @Input() hideActionButton = false;
  @Output() viewDetails = new EventEmitter<Coin>();

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
    // Use backend confidence if available (it's 0-100, convert to 0-1)
    if (this.coin.confidence !== undefined && this.coin.confidence !== null) {
      return this.coin.confidence / 100;
    }
    
    // Fallback: calculate from sentiment scores if confidence not available
    if (!this.coin.hype && !this.coin.communityHype && !this.coin.popularity) {
      return 0;
    }
    const hype = this.coin.hype || 0;
    const community = this.coin.communityHype || 0;
    const popularity = this.coin.popularity || 0;

    // Weighted average: 30% hype, 50% community, 20% popularity (matching backend)
    return (hype * 0.3 + community * 0.5 + popularity * 0.2);
  }

  getConfidenceColor(): string {
    const confidence = this.calculateConfidence();
    // Use recommendation if available, otherwise use confidence thresholds
    if (this.coin.recommendation) {
      if (this.coin.recommendation === 'BUY') return '#00d4aa'; // Green
      if (this.coin.recommendation === 'HOLD') return '#fbbf24'; // Orange/Yellow
      if (this.coin.recommendation === 'SELL') return '#ff6b6b'; // Red
    }
    // Fallback to confidence-based colors
    if (confidence >= 0.6) return '#00d4aa'; // Green
    if (confidence >= 0.4) return '#fbbf24'; // Orange/Yellow
    return '#ff6b6b'; // Red
  }

  onViewDetails(): void {
    this.viewDetails.emit(this.coin);
  }

  onImageError(event: Event): void {
    // Hide the broken image and show fallback text
    const img = event.target as HTMLImageElement;
    img.style.display = 'none';
    const fallback = img.parentElement?.querySelector('.coin-icon-text');
    if (fallback) {
      (fallback as HTMLElement).style.display = 'flex';
    }
  }
}

