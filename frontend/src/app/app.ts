import { Component, signal } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router';
import { Sidebar } from './sidebar/sidebar';
import { CommonModule } from '@angular/common';
import { ProfileBadge } from './profile-badge/profile-badge'; // 1. Import ProfileBadge

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    Sidebar,
    ProfileBadge // 2. Add ProfileBadge to imports
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  isSidebarCollapsed = signal(false);
  constructor(private router: Router) {}

  toggleSidebar() {
    this.isSidebarCollapsed.set(!this.isSidebarCollapsed());
  }

  isLoginPage(): boolean {
    return this.router.url === '/login';
  }
}