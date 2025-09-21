import { Component, HostListener, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class Chat {
  // --- State for Chat Overlay ---
  isChatCollapsed = signal(false);

  // --- State for Resizing ---
  summaryWidth = signal(280);
  chatHeightVh = signal(25);
  isResizingWidth = false;
  isResizingHeight = false;
  isDragging = signal(false);

  toggleChat() {
    this.isChatCollapsed.set(!this.isChatCollapsed());
  }

  // --- Logic for Resizing ---
  startResize(event: MouseEvent, direction: 'width' | 'height') {
    if (direction === 'width') {
      this.isResizingWidth = true;
    } else {
      this.isResizingHeight = true;
      // === THIS IS THE FIX ===
      // If chat is collapsed, un-collapse it when resize starts.
      if (this.isChatCollapsed()) {
        this.isChatCollapsed.set(false);
      }
    }
    this.isDragging.set(true);
    event.preventDefault();
  }

  @HostListener('window:mousemove', ['$event'])
  onResize(event: MouseEvent) {
    if (this.isResizingWidth) {
      const newWidth = window.innerWidth - event.clientX;
      if (newWidth > 250 && newWidth < 600) {
        this.summaryWidth.set(newWidth);
      }
    }
    if (this.isResizingHeight) {
      const newHeight = ((window.innerHeight - event.clientY) / window.innerHeight) * 100;
      if (newHeight > 15 && newHeight < 90) {
        this.chatHeightVh.set(newHeight);
      }
    }
  }

  @HostListener('window:mouseup')
  stopResize() {
    this.isResizingWidth = false;
    this.isResizingHeight = false;
    this.isDragging.set(false);
  }
}