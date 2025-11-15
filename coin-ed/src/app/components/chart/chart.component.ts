import { Component, ElementRef, ViewChild, AfterViewInit, inject, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-chart',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart.component.html',
  styleUrls: ['./chart.component.css']
})
export class ChartComponent implements AfterViewInit {
  @ViewChild('chartCanvas') chartCanvas!: ElementRef<HTMLCanvasElement>;
  private chart: Chart | null = null;
  dataService = inject(DataService);
  selectedTimeframe = '1h';
  selectedCoin = 'Bitcoin/BTC';

  timeframes = ['1h', '3h', '1d', '1w', '1m'];

  constructor() {
    effect(() => {
      // React to data changes
      const coins = this.dataService.coins();
      if (coins.length > 0 && this.chart) {
        this.updateChart();
      }
    });
  }

  ngAfterViewInit(): void {
    this.initChart();
  }

  private initChart(): void {
    const ctx = this.chartCanvas.nativeElement.getContext('2d');
    if (!ctx) return;

    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(255, 215, 0, 0.3)');
    gradient.addColorStop(1, 'rgba(255, 215, 0, 0)');

    const labels = this.generateTimeLabels();
    const data = this.generateChartData();

    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Price',
            data,
            borderColor: '#FFD700',
            backgroundColor: gradient,
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 6,
            pointHoverBackgroundColor: '#FFD700',
            pointHoverBorderColor: '#fff',
            pointHoverBorderWidth: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index'
        },
        plugins: {
          legend: {
            display: false
          },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              padding: 12,
              displayColors: false,
              callbacks: {
                label: (context) => `$${context.parsed.y?.toLocaleString() || '0'}`
              }
            }
        },
        scales: {
          x: {
            grid: {
              display: false
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.5)',
              maxRotation: 0
            }
          },
          y: {
            position: 'right',
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: 'rgba(255, 255, 255, 0.5)',
              callback: (value) => `$${(value as number).toLocaleString()}`
            }
          }
        }
      }
    });
  }

  private updateChart(): void {
    if (!this.chart) return;

    this.chart.data.datasets[0].data = this.generateChartData();
    this.chart.update('none');
  }

  private generateTimeLabels(): string[] {
    const labels: string[] = [];
    const now = new Date();
    for (let i = 50; i >= 0; i--) {
      const date = new Date(now.getTime() - i * 30 * 60000);
      labels.push(
        date.toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
        })
      );
    }
    return labels;
  }

  generateChartData(): number[] {
    const coins = this.dataService.coins();
    if (coins.length > 0 && coins[0].chartData) {
      return coins[0].chartData;
    }

    // Fallback mock data
    const data: number[] = [];
    let base = 38252;
    for (let i = 0; i < 51; i++) {
      base += (Math.random() - 0.48) * 2000;
      data.push(base);
    }
    return data;
  }

  selectTimeframe(timeframe: string): void {
    this.selectedTimeframe = timeframe;
    // In a real app, this would fetch different data based on timeframe
  }

  onCoinChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.selectedCoin = target.value;
    this.updateChart();
  }
}

