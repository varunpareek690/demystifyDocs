import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { Settings } from '../settings/settings';
import { chatHistoryData } from '../mock-data';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, Settings, RouterModule],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css'
})
export class Sidebar {
  @Input() isCollapsed = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  isSettingsOpen = signal(false);
  
  // Expose mock data to the template
  chatHistory = chatHistoryData;

  constructor(private router: Router, public route: ActivatedRoute) {}

  onMenuClick() {
    this.toggleSidebar.emit();
  }

  createNewChat() {
    // Navigate to the welcome page to start a new chat flow
    this.router.navigate(['/welcome']);
  }

  toggleSettings() {
    this.isSettingsOpen.set(!this.isSettingsOpen());
  }
}