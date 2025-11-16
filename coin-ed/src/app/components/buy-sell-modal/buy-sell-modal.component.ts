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

  close = output<void>();
  actionConfirmed = output<{ agentType: AgentType; action: ActionType }>();

  open(type: AgentType): void {
    this.agentType.set(type);
    this.isOpen.set(true);
    
    // Auto-select the action based on agent type
    const action = type === 'buyer' ? 'buy' : 'sell';
    this.selectedAction.set(action);
  }

  closeModal(): void {
    this.isOpen.set(false);
    this.selectedAction.set(null);
    this.close.emit();
  }

  selectAction(action: ActionType): void {
    this.selectedAction.set(action);
  }

  confirmAction(): void {
    if (this.selectedAction()) {
      const action = this.selectedAction()!;
      
      this.actionConfirmed.emit({
        agentType: this.agentType(),
        action: action
      });
      
      // Close modal immediately
      this.closeModal();
    }
  }
}
