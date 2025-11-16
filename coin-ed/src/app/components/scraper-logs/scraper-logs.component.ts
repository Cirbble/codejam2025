import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { ScraperService } from '../../services/scraper.service';

@Component({
  selector: 'app-scraper-logs',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="scraper-logs">
      <div class="logs-header">
        <h4>Live Scraper Logs</h4>
        <span class="log-count">{{ logs().length }} messages</span>
      </div>
      <div class="logs-container">
        @for (log of logs(); track $index) {
          <div class="log-entry">{{ log }}</div>
        }
        @empty {
          <div class="no-logs">No logs yet. Enable scraper to start...</div>
        }
      </div>
    </div>
  `,
  styles: [`
    .scraper-logs {
      background: rgba(20, 20, 20, 0.8);
      border-radius: 12px;
      padding: 16px;
      margin-top: 20px;
      max-height: 300px;
      display: flex;
      flex-direction: column;
    }

    .logs-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .logs-header h4 {
      color: #fff;
      font-size: 14px;
      font-weight: 600;
      margin: 0;
    }

    .log-count {
      background: rgba(0, 212, 170, 0.2);
      color: #00d4aa;
      padding: 4px 8px;
      border-radius: 8px;
      font-size: 11px;
      font-weight: 700;
    }

    .logs-container {
      flex: 1;
      overflow-y: auto;
      font-family: 'Courier New', monospace;
      font-size: 12px;
    }

    .logs-container::-webkit-scrollbar {
      width: 6px;
    }

    .logs-container::-webkit-scrollbar-track {
      background: rgba(255, 255, 255, 0.05);
    }

    .logs-container::-webkit-scrollbar-thumb {
      background: rgba(0, 212, 170, 0.3);
      border-radius: 3px;
    }

    .log-entry {
      color: rgba(255, 255, 255, 0.7);
      padding: 4px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .log-entry:last-child {
      border-bottom: none;
    }

    .no-logs {
      color: rgba(255, 255, 255, 0.4);
      text-align: center;
      padding: 40px 20px;
      font-style: italic;
    }
  `]
})
export class ScraperLogsComponent {
  private scraperService = inject(ScraperService);

  logs = toSignal(this.scraperService.scraperLogs$, { initialValue: [] });
}

