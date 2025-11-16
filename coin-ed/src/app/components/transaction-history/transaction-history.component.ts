import { Component, inject, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DataService } from '../../services/data.service';
import { Transaction } from '../../models/coin.model';

@Component({
  selector: 'app-transaction-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './transaction-history.component.html',
  styleUrls: ['./transaction-history.component.css']
})
export class TransactionHistoryComponent {
  dataService = inject(DataService);
  @Output() close = new EventEmitter<void>();

  getTransactions(): Transaction[] {
    return this.dataService.getTransactions();
  }

  getTotalBuyAmount(): number {
    return this.dataService.getTotalBuyAmount();
  }

  getTotalSellAmount(): number {
    return this.dataService.getTotalSellAmount();
  }

  getNetAmount(): number {
    return this.getTotalSellAmount() - this.getTotalBuyAmount();
  }

  clearHistory(): void {
    if (confirm('Are you sure you want to clear all transaction history?')) {
      this.dataService.clearTransactions();
    }
  }

  onClose(): void {
    this.close.emit();
  }

  formatDate(date: Date): string {
    return new Date(date).toLocaleString();
  }

  formatTime(date: Date): string {
    return new Date(date).toLocaleTimeString();
  }
}
