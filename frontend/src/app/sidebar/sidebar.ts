import { Component, Input, Output, EventEmitter, signal } from '@angular/core'; // 1. Import signal
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Settings } from '../settings/settings'; // 2. Import the Settings component

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, Settings], // 3. Add Settings to the imports array
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css'
})
export class Sidebar {
  @Input() isCollapsed = false;
  @Output() toggleSidebar = new EventEmitter<void>();

  // 4. Add a signal to control the settings modal's visibility
  isSettingsOpen = signal(false);

  constructor(private router: Router) {}

  onMenuClick() {
    this.toggleSidebar.emit();
  }

  createNewChat() {
    this.router.navigate(['/']);
  }

  // 5. Create a function to open/close the modal
  toggleSettings() {
    this.isSettingsOpen.set(!this.isSettingsOpen());
  }
}