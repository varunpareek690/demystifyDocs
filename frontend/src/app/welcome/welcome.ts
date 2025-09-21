import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FileUploadService, UploadProgress, DocumentUploadResponse } from '../services/file-upload.service';

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './welcome.html',
  styleUrl: './welcome.css'
})
export class Welcome {
  // Upload state
  isUploading = signal(false);
  uploadProgress = signal<UploadProgress>({ progress: 0, status: 'uploading' });
  selectedFile = signal<File | null>(null);
  uploadError = signal<string | null>(null);
  uploadSuccess = signal<DocumentUploadResponse | null>(null);

  // Drag and drop state
  isDragOver = signal(false);

  constructor(
    private router: Router,
    private fileUploadService: FileUploadService
  ) {}

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
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                         'text/plain'];
    
    if (!allowedTypes.includes(file.type)) {
      this.uploadError.set('Please upload a PDF, DOC, DOCX, or TXT file');
      return;
    }

    // Validate file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      this.uploadError.set('File size must be less than 10MB');
      return;
    }

    this.selectedFile.set(file);
    this.uploadError.set(null);
    this.startUpload(file);
  }

  private startUpload(file: File) {
    this.isUploading.set(true);
    this.fileUploadService.resetProgress();

    // Subscribe to upload progress
    this.fileUploadService.getUploadProgress().subscribe(progress => {
      this.uploadProgress.set(progress);
    });

    // Perform the upload
    this.fileUploadService.uploadFile(file).subscribe({
      next: (response) => {
        if (response) {
          this.uploadSuccess.set(response);
          this.isUploading.set(false);
          
          // Navigate to chat with the new session
          if (response.data.chat_session) {
            setTimeout(() => {
              this.router.navigate(['/chat', response.data.chat_session.id], {
                state: { 
                  document: response.data.document,
                  summary: response.data.summary,
                  suggestedQuestions: response.data.suggested_questions
                }
              });
            }, 1500);
          } else {
            // Fallback navigation
            setTimeout(() => {
              this.router.navigate(['/chat']);
            }, 1500);
          }
        }
      },
      error: (error) => {
        this.isUploading.set(false);
        this.uploadError.set(error.error?.detail || 'Upload failed. Please try again.');
        console.error('Upload error:', error);
      }
    });
  }

  navigateToChat(): void {
    if (this.uploadSuccess()) {
      const response = this.uploadSuccess()!;
      if (response.data.chat_session) {
        this.router.navigate(['/chat', response.data.chat_session.id]);
      } else {
        this.router.navigate(['/chat']);
      }
    } else {
      this.router.navigate(['/chat']);
    }
  }

  resetUpload() {
    this.selectedFile.set(null);
    this.uploadError.set(null);
    this.uploadSuccess.set(null);
    this.isUploading.set(false);
    this.fileUploadService.resetProgress();
  }

  // Helper methods for template
  getProgressWidth(): string {
    return `${this.uploadProgress().progress}%`;
  }

  getStatusMessage(): string {
    const progress = this.uploadProgress();
    if (progress.message) return progress.message;
    
    switch (progress.status) {
      case 'uploading': return 'Uploading file...';
      case 'processing': return 'Processing document...';
      case 'completed': return 'Document processed successfully!';
      case 'error': return 'Upload failed';
      default: return '';
    }
  }
}