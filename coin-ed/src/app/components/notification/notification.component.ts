import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface BuyNotification {
  id: number;
  coinName: string;
  amount: number;
  visible: boolean;
}

@Component({
  selector: 'app-notification',
  standalone: true,
  imports: [CommonModule],
  template: `
    @for (notification of notifications(); track notification.id) {
      <div class="notification" [class.visible]="notification.visible">
        <div class="notification-content">
          <div class="notification-title">AI Buy Executed</div>
          <div class="notification-message">
            Bought \${{ notification.amount.toFixed(2) }} worth of {{ notification.coinName }}
          </div>
        </div>
        <button class="notification-close" (click)="removeNotification(notification.id)">×</button>
      </div>
    }
  `,
  styles: [`
    :host {
      position: fixed !important;
      bottom: 24px !important;
      left: 24px !important;
      right: auto !important;
      top: auto !important;
      z-index: 9999 !important;
      display: flex !important;
      flex-direction: column !important;
      gap: 12px;
      max-width: 400px;
      pointer-events: none;
    }

    .notification {
      display: flex;
      align-items: center;
      gap: 12px;
      background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%);
      border: 1px solid rgba(0, 212, 170, 0.3);
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 212, 170, 0.2);
      opacity: 0;
      transform: translateX(-400px);
      transition: all 0.3s ease;
      pointer-events: auto;
      min-width: 300px;
    }

    .notification.visible {
      opacity: 1;
      transform: translateX(0);
    }

    .notification-content {
      flex: 1;
    }

    .notification-title {
      color: #00d4aa;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
    }

    .notification-message {
      color: rgba(255, 255, 255, 0.8);
      font-size: 13px;
      line-height: 1.4;
    }

    .notification-close {
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.5);
      font-size: 24px;
      cursor: pointer;
      transition: color 0.2s ease;
      line-height: 1;
      padding: 0;
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .notification-close:hover {
      color: #fff;
    }

    @media (max-width: 768px) {
      :host {
        bottom: 16px;
        left: 16px;
        right: 16px;
        max-width: none;
      }
    }
  `]
})
export class NotificationComponent {
  notifications = signal<BuyNotification[]>([]);
  private nextId = 0;

  showBuyNotification(coinName: string, amount: number): void {
    const notification: BuyNotification = {
      id: this.nextId++,
      coinName,
      amount,
      visible: false
    };

    this.notifications.set([...this.notifications(), notification]);

    setTimeout(() => {
      const notifications = this.notifications().map(n => 
        n.id === notification.id ? { ...n, visible: true } : n
      );
      this.notifications.set(notifications);
    }, 10);
  }

  removeNotification(id: number): void {
    const notifications = this.notifications().map(n => 
      n.id === id ? { ...n, visible: false } : n
    );
    this.notifications.set(notifications);

    setTimeout(() => {
      this.notifications.set(this.notifications().filter(n => n.id !== id));
    }, 300);
  }
}
