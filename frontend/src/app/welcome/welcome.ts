import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { chatHistoryData } from '../mock-data';

interface UploadProgress {
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './welcome.html',
  styleUrl: './welcome.css'
})
export class Welcome {
  isUploading = signal(false);
  uploadProgress = signal<UploadProgress>({ progress: 0, status: 'uploading' });
  selectedFile = signal<File | null>(null);
  uploadError = signal<string | null>(null);
  uploadSuccess = signal<boolean>(false);
  isDragOver = signal(false);

  constructor(private router: Router) {}

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.handleFile(input.files[0]);
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragOver.set(false);
    const files = event.dataTransfer?.files;
    if (files && files[0]) {
      this.handleFile(files[0]);
    }
  }

  private handleFile(file: File) {
    this.resetUpload();
    this.selectedFile.set(file);
  }

  // This method simulates the upload and updates the state to success
  startProcessing() {
    if (!this.selectedFile()) return;

    this.isUploading.set(true);
    setTimeout(() => this.uploadProgress.set({ progress: 45, status: 'uploading', message: 'Uploading file...' }), 500);
    setTimeout(() => this.uploadProgress.set({ progress: 80, status: 'processing', message: 'Processing document...' }), 1500);

    setTimeout(() => {
      this.isUploading.set(false);
      this.uploadSuccess.set(true); // Set success to true, but DO NOT navigate yet
    }, 2500);
  }

  // This method is called by the button AFTER success
  proceedToChat() {
    // Navigate to the first mock chat to simulate a new session
    this.router.navigate(['/chat', chatHistoryData[0].id]);
  }

  resetUpload() {
    this.selectedFile.set(null);
    this.uploadError.set(null);
    this.uploadSuccess.set(false);
    this.isUploading.set(false);
    this.uploadProgress.set({ progress: 0, status: 'uploading' });
  }

  getProgressWidth(): string {
    return `${this.uploadProgress().progress}%`;
  }

  getStatusMessage(): string {
    return this.uploadProgress().message || 'Starting...';
  }
}