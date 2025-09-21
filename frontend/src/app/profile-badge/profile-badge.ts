import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../auth.service';

@Component({
  selector: 'app-profile-badge',
  standalone: true,
  imports: [CommonModule],

  templateUrl: './profile-badge.html',
  styleUrl: './profile-badge.css'
})
export class ProfileBadge {
  isPopoverOpen = signal(false);

  constructor(public authService: AuthService) {}

  // ADD THIS GETTER
  // It safely gets the first name from the user's full name
  get firstName(): string {
    const user = this.authService.currentUser();
    // If there's a user and a name, split the name and return the first part. Otherwise, return an empty string.
    return user?.name?.split(' ')[0] || '';
  }

  togglePopover() {
    this.isPopoverOpen.set(!this.isPopoverOpen());
  }

  logout() {
    this.authService.logout();
  }
}
