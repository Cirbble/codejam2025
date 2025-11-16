import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-gauge',
  imports: [CommonModule],
  templateUrl: './gauge.html',
  styleUrl: './gauge.css'
})
export class GaugeComponent {
  @Input() value: number = 0; // 0 to 1
  @Input() label: string = '';
  @Input() color: string = '#6B8AFF';

  getPercentage(): number {
    return Math.round(this.value * 100);
  }
}
