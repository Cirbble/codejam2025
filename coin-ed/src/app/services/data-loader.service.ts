import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DataService } from './data.service';

@Injectable({
  providedIn: 'root'
})
export class DataLoaderService {
  private http = inject(HttpClient);
  private dataService = inject(DataService);

  /**
   * Load data from a JSON file
   */
  loadFromFile(filePath: string): void {
    this.http.get(filePath).subscribe({
      next: (data: any) => {
        if (data.coins && Array.isArray(data.coins)) {
          data.coins.forEach((coin: any) => {
            this.dataService.parseScrapedData(coin);
          });
        } else {
          this.dataService.parseScrapedData(data);
        }
      },
      error: (error) => {
        console.error('Error loading data:', error);
      }
    });
  }

  /**
   * Simulate receiving data from websocket or API
   */
  simulateIncomingData(data: any): void {
    this.dataService.parseScrapedData(data);
  }
}

