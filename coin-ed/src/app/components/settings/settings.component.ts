import { Component, signal, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { DataService } from '../../services/data.service';

@Component({
  selector: 'app-settings',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class SettingsComponent {
  private router = inject(Router);
  private fb = inject(FormBuilder);
  dataService = inject(DataService);

  accountForm: FormGroup;
  balanceForm: FormGroup;
  isSignedIn = signal(false);
  notification = signal<{message: string, type: 'success' | 'error'} | null>(null);
  isLoginMode = signal(false);

  constructor() {
    this.accountForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      cardNumber: ['', [Validators.required, Validators.pattern(/^\d{16}$/)]],
      expirationDate: ['', [Validators.required, Validators.pattern(/^(0[1-9]|1[0-2])\/\d{2}$/)]],
      cardHolder: ['', [Validators.required]],
      cvv: ['', [Validators.required, Validators.pattern(/^\d{3,4}$/)]]
    });

    this.balanceForm = this.fb.group({
      balance: [this.dataService.getAccountBalance(), [Validators.required, Validators.min(0)]]
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  signIn(): void {
    if (this.accountForm.valid) {
      this.isSignedIn.set(true);
      console.log('Account details saved:', this.accountForm.value);
      this.notification.set({message: 'Successfully signed in! Your account details have been saved.', type: 'success'});
      setTimeout(() => this.notification.set(null), 3000);
    } else {
      this.notification.set({message: 'Please fill in all required fields correctly before signing in.', type: 'error'});
      setTimeout(() => this.notification.set(null), 3000);
    }
  }

  signOut(): void {
    this.isSignedIn.set(false);
    this.accountForm.reset();
  }

  toggleMode(): void {
    this.isLoginMode.update(mode => !mode);
    this.accountForm.reset();
  }

  updateBalance(): void {
    if (this.balanceForm.valid) {
      const newBalance = this.balanceForm.value.balance;
      this.dataService.setAccountBalance(newBalance);
      this.notification.set({message: `Account balance updated to $${newBalance.toLocaleString()}`, type: 'success'});
      setTimeout(() => this.notification.set(null), 3000);
    } else {
      this.notification.set({message: 'Please enter a valid balance amount', type: 'error'});
      setTimeout(() => this.notification.set(null), 3000);
    }
  }

  getCurrentBalance(): number {
    return this.dataService.getAccountBalance();
  }
}
