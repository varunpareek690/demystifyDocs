import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router'; // 1. Import Router

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './settings.html',
  styleUrl: './settings.css'
})
export class Settings {
  @Output() closeModal = new EventEmitter<void>();

  // 2. Inject Router
  constructor(private router: Router) {}

  onClose() {
    this.closeModal.emit();
  }

  // 3. Create navigation function
  navigateToFeature() {
    this.onClose(); // Close the modal first
    this.router.navigate(['/feature-in-progress']);
  }
}