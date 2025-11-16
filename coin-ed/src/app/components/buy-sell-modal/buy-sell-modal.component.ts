import { Component, signal, output } from '@angular/core';
import { CommonModule } from '@angular/common';

export type ActionType = 'buy' | 'sell';
export type AgentType = 'buyer' | 'seller';

@Component({
  selector: 'app-buy-sell-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './buy-sell-modal.component.html',
  styleUrls: ['./buy-sell-modal.component.css']
})
export class BuySellModalComponent {
  isOpen = signal(false);
  agentType = signal<AgentType>('buyer');
  selectedAction = signal<ActionType | null>(null);
  generatedMessage = signal<string>('');
  successMessage = signal<string>('');
  showSuccess = signal(false);
  currencies = signal<string[]>([]);
  visibleCurrencies = signal<Set<string>>(new Set());

  close = output<void>();
  actionSelected = output<{ agentType: AgentType; action: ActionType }>();

  open(type: AgentType): void {
    this.agentType.set(type);
    this.selectedAction.set(null);
    this.generatedMessage.set('');
    this.successMessage.set('');
    this.showSuccess.set(false);
    this.currencies.set([]);
    this.visibleCurrencies.set(new Set());
    this.isOpen.set(true);
    
    // Auto-select the action based on agent type
    const action = type === 'buyer' ? 'buy' : 'sell';
    this.selectAction(action);
  }

  closeModal(): void {
    this.isOpen.set(false);
    this.selectedAction.set(null);
    this.generatedMessage.set('');
    this.successMessage.set('');
    this.showSuccess.set(false);
    this.currencies.set([]);
    this.visibleCurrencies.set(new Set());
    this.close.emit();
  }

  selectAction(action: ActionType): void {
    this.selectedAction.set(action);
    this.generateMessage(action);
  }

  private generateRandomCurrencies(): string[] {
    const availableCurrencies = [
      'BTC', 'ETH', 'SOL', 'DOGE', 'PEPE', 'SHIB', 'BONK', 'WIF',
      'ADA', 'DOT', 'MATIC', 'AVAX', 'LINK', 'UNI', 'AAVE', 'ATOM'
    ];
    
    // Generate 2-5 random currencies
    const count = Math.floor(Math.random() * 4) + 2; // 2 to 5
    const shuffled = [...availableCurrencies].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
  }

  private generateMessage(action: ActionType): void {
    const agentName = this.agentType() === 'buyer' ? 'AI Buyer' : 'AI Seller';
    
    if (action === 'buy') {
      const buyMessages = [
        `${agentName} Agent: Analyzing market conditions... Strong buy signal detected! 📈`,
        `${agentName} Agent: Positive sentiment indicators identified. Initiating purchase sequence... 💰`,
        `${agentName} Agent: Market opportunity detected. Executing buy order based on sentiment analysis. 🎯`,
        `${agentName} Agent: Community sentiment favorable. Recommended action: BUY. Proceeding with transaction... ✅`,
        `${agentName} Agent: Technical indicators align with positive social sentiment. Buy order placed! 🚀`
      ];
      this.generatedMessage.set(buyMessages[Math.floor(Math.random() * buyMessages.length)]);
    } else {
      const sellMessages = [
        `${agentName} Agent: Market analysis complete. Sell signal triggered for risk management. 📉`,
        `${agentName} Agent: Sentiment indicators suggest optimal exit point. Initiating sell order... 💸`,
        `${agentName} Agent: Profit-taking opportunity identified. Executing sell strategy... 📊`,
        `${agentName} Agent: Risk assessment recommends position reduction. Sell order in progress... ⚠️`,
        `${agentName} Agent: Market conditions favor exit. Securing gains through strategic sell... ✅`
      ];
      this.generatedMessage.set(sellMessages[Math.floor(Math.random() * sellMessages.length)]);
    }
  }

  private showCurrenciesWithDelay(currencies: string[]): void {
    // Show each currency with a random delay between 200-800ms
    currencies.forEach((currency, index) => {
      const randomDelay = Math.floor(Math.random() * 600) + 200; // 200-800ms
      const cumulativeDelay = index * randomDelay;
      
      setTimeout(() => {
        const current = new Set(this.visibleCurrencies());
        current.add(currency);
        this.visibleCurrencies.set(current);
      }, cumulativeDelay);
    });
  }

  isCurrencyVisible(currency: string): boolean {
    return this.visibleCurrencies().has(currency);
  }

  confirmAction(): void {
    if (this.selectedAction()) {
      const action = this.selectedAction()!;
      
      this.actionSelected.emit({
        agentType: this.agentType(),
        action: action
      });
      
      // Generate random currencies
      const selectedCurrencies = this.generateRandomCurrencies();
      this.currencies.set(selectedCurrencies);
      
      // Wait a bit before showing success message
      setTimeout(() => {
        this.showSuccess.set(true);
        // Start showing currencies one by one with random delays
        this.showCurrenciesWithDelay(selectedCurrencies);
      }, 2000);
    }
  }
}
