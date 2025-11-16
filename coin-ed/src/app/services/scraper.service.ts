import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject } from 'rxjs';

export interface ScraperStatus {
  running: boolean;
  pid: number | null;
}

export interface ScraperUpdate {
  type: 'scraper_update' | 'scraper_log' | 'scraper_stopped' | 'initial_data' | 'coin_data_updated' | 'thread_update';
  data?: any[];
  message?: string;
  code?: number;
  timestamp: string;
  coins?: number;
  clientId?: string;
  threadId?: string; // For thread-specific updates (altcoin, CryptoMoonShots, pumpfun)
}

@Injectable({ providedIn: 'root' })
export class ScraperService {
  private ws: WebSocket | null = null;
  private isBrowser = false;

  // Point directly to backend; backend enables CORS so cross-origin is fine in dev
  private backendBase = 'http://localhost:3000';

  private scraperStatusSubject = new BehaviorSubject<ScraperStatus>({ running: false, pid: null });
  private scraperDataSubject = new BehaviorSubject<any[]>([]);
  private scraperLogsSubject = new BehaviorSubject<string[]>([]);
  private connectedSubject = new BehaviorSubject<boolean>(false);

  public scraperStatus$ = this.scraperStatusSubject.asObservable();
  public scraperData$ = this.scraperDataSubject.asObservable();
  public scraperLogs$ = this.scraperLogsSubject.asObservable();
  public connected$ = this.connectedSubject.asObservable();

  private logs: string[] = [];
  private reconnectDelay = 2000; // start at 2s

  constructor(@Inject(PLATFORM_ID) platformId: Object) {
    this.isBrowser = isPlatformBrowser(platformId);

    if (this.isBrowser) {
      this.connectWebSocket();
      this.checkStatus();
    }
  }

  private connectWebSocket(): void {
    if (!this.isBrowser) return;

    // Close existing connection if any
    if (this.ws) {
      try {
        this.ws.close();
      } catch (e) {
        // Ignore errors on close
      }
      this.ws = null;
    }

    try {
      const isHttps = window.location.protocol === 'https:';
      const proto = isHttps ? 'wss' : 'ws';
      const url = `${proto}://${new URL(this.backendBase).host}/ws`;

      console.log(`[WebSocket] Connecting to ${url}...`);
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.connectedSubject.next(true);
        this.reconnectDelay = 2000; // reset
        console.log('[WebSocket] Connected successfully');
        this.addLog('✅ Connected to scraper backend');
      };

      this.ws.onmessage = (event) => {
        try {
          const update: ScraperUpdate = JSON.parse(event.data);
          this.handleUpdate(update);
        } catch (error) {
          console.error('[WebSocket] Error parsing message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        this.connectedSubject.next(false);
      };

      this.ws.onclose = (event) => {
        console.log(`[WebSocket] Disconnected (code: ${event.code}, reason: ${event.reason})`);
        this.connectedSubject.next(false);

        // Only reconnect if not a normal closure
        if (event.code !== 1000) {
          this.addLog(`WebSocket disconnected. Reconnecting in ${(this.reconnectDelay / 1000).toFixed(0)}s...`);
          setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
          // Exponential backoff up to 30s
          this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
        } else {
          this.addLog('WebSocket closed normally');
        }
      };
    } catch (error) {
      console.error('[WebSocket] Failed to connect:', error);
      this.connectedSubject.next(false);
      setTimeout(() => this.connectWebSocket(), this.reconnectDelay);
    }
  }

  private handleUpdate(update: ScraperUpdate): void {
    switch (update.type) {
      case 'initial_data':
        if (update.data) {
          this.scraperDataSubject.next(update.data);
          this.addLog(`Initial scraped posts loaded (${update.data.length})`);
        }
        if (update.clientId) {
          console.log(`[WebSocket] Client ID: ${update.clientId}`);
        }
        break;
      case 'scraper_update':
        if (update.data) {
          this.scraperDataSubject.next(update.data);
          this.addLog(`Received ${update.data.length} posts from scraper`);
        }
        break;
      case 'scraper_log':
        if (update.message) this.addLog(update.message);
        break;
      case 'thread_update':
        // Thread-specific update from one of the 3 parallel scrapers
        if (update.threadId && update.message) {
          this.addLog(`[${update.threadId}] ${update.message}`);
        }
        break;
      case 'coin_data_updated':
        this.addLog(`✅ Coin data updated (${update.coins || 0} coins)`);
        // Notify data service via a custom event for reload
        window.dispatchEvent(new CustomEvent('coin-data-updated'));
        break;
      case 'scraper_stopped':
        this.scraperStatusSubject.next({ running: false, pid: null });
        this.addLog('Scraper stopped');
        // Do not force reload here; wait for coin_data_updated after conversion
        break;
    }
  }

  private addLog(message: string): void {
    const timestamp = new Date().toLocaleTimeString();
    this.logs.push(`[${timestamp}] ${message}`);
    if (this.logs.length > 300) this.logs = this.logs.slice(-300);
    this.scraperLogsSubject.next([...this.logs]);
  }

  async startScraper(): Promise<boolean> {
    if (!this.isBrowser) return false;
    try {
      const res = await fetch(`${this.backendBase}/api/scraper/start`, { method: 'POST' });
      const result = await res.json();
      if (result.success) {
        this.scraperStatusSubject.next({ running: true, pid: result.pid });
        this.addLog('Scraper started successfully');
        this.scraperDataSubject.next([]);
        return true;
      } else {
        this.addLog(`Failed to start scraper: ${result.message}`);
        return false;
      }
    } catch (e) {
      this.addLog('Error starting scraper - backend offline?');
      return false;
    }
  }

  async stopScraper(): Promise<boolean> {
    if (!this.isBrowser) return false;
    try {
      const res = await fetch(`${this.backendBase}/api/scraper/stop`, { method: 'POST' });
      const result = await res.json();
      if (result.success) {
        this.scraperStatusSubject.next({ running: false, pid: null });
        this.addLog('Scraper stopped successfully');
        return true;
      } else {
        this.addLog(`Failed to stop scraper: ${result.message}`);
        return false;
      }
    } catch (e) {
      this.addLog('Error stopping scraper');
      return false;
    }
  }

  async checkStatus(): Promise<void> {
    if (!this.isBrowser) return;
    try {
      const res = await fetch(`${this.backendBase}/api/scraper/status`);
      const status = await res.json();
      this.scraperStatusSubject.next(status);
    } catch {
      this.scraperStatusSubject.next({ running: false, pid: null });
    }
  }
}
