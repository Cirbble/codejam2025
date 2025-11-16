import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'buy' | 'sell';
  timestamp: Date;
}

@Component({
  selector: 'app-notification',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './notification.component.html',
  styleUrls: ['./notification.component.css']
})
export class NotificationComponent implements OnInit, OnDestroy {
  notifications: Notification[] = [];
  private notificationIdCounter = 0;

  ngOnInit(): void {}

  ngOnDestroy(): void {
    this.notifications = [];
  }

  addNotification(message: string, type: 'buy' | 'sell' = 'buy', title?: string): void {
    const notification: Notification = {
      id: this.notificationIdCounter++,
      title: title || (type === 'buy' ? 'Agent Executed Buy' : 'Agent Executed Sell'),
      message,
      type,
      timestamp: new Date()
    };

    this.notifications.push(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      this.removeNotification(notification.id);
    }, 5000);
  }

  removeNotification(id: number): void {
    this.notifications = this.notifications.filter(n => n.id !== id);
  }
}
