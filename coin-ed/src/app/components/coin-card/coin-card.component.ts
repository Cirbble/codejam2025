import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Coin } from '../../models/coin.model';

@Component({
  selector: 'app-coin-card',
  standalone: true,
  imports: [CommonModule],
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
}

