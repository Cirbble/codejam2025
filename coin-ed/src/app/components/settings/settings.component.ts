import { Component, signal, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';

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

  accountForm: FormGroup;
  isSignedIn = signal(false);

  constructor() {
    this.accountForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      cardNumber: ['', [Validators.required, Validators.pattern(/^\d{16}$/)]],
      expirationDate: ['', [Validators.required, Validators.pattern(/^(0[1-9]|1[0-2])\/\d{2}$/)]],
      cardHolder: ['', [Validators.required]],
      cvv: ['', [Validators.required, Validators.pattern(/^\d{3,4}$/)]]
    });
  }

  goBack(): void {
    this.router.navigate(['/']);
  }

  signIn(): void {
    if (this.accountForm.valid) {
      this.isSignedIn.set(true);
      console.log('Account details saved:', this.accountForm.value);
    }
  }

  signOut(): void {
    this.isSignedIn.set(false);
    this.accountForm.reset();
  }
}
