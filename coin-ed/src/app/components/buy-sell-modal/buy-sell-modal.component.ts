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

  close = output<void>();
  actionSelected = output<{ agentType: AgentType; action: ActionType }>();

  open(type: AgentType): void {
    this.agentType.set(type);
    this.selectedAction.set(null);
    this.generatedMessage.set('');
    this.successMessage.set('');
    this.showSuccess.set(false);
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
    this.close.emit();
  }

  selectAction(action: ActionType): void {
    this.selectedAction.set(action);
    this.generateMessage(action);
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

  confirmAction(): void {
    if (this.selectedAction()) {
      const action = this.selectedAction()!;
      
      this.actionSelected.emit({
        agentType: this.agentType(),
        action: action
      });
      
      // Show success message
      this.showSuccess.set(true);
      this.successMessage.set(
        action === 'buy' 
          ? '✅ Successfully bought!' 
          : '✅ Successfully sold!'
      );
      
      // Close modal after showing success message
      setTimeout(() => {
        this.closeModal();
      }, 2000);
    }
  }
}
