import { Component, signal } from '@angular/core';
import { Router, RouterOutlet } from '@angular/router'; // Import Router
import { Sidebar } from './sidebar/sidebar';
import { CommonModule } from '@angular/common'; // Import CommonModule for *ngIf

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule, // Add CommonModule here
    RouterOutlet,
    Sidebar
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  isSidebarCollapsed = signal(false);

  // Inject the Router so we can check the current URL
  constructor(private router: Router) {}

  toggleSidebar() {
    this.isSidebarCollapsed.set(!this.isSidebarCollapsed());
  }

  // This function checks if the current page is the login page
  isLoginPage(): boolean {
    return this.router.url === '/login';
  }
}