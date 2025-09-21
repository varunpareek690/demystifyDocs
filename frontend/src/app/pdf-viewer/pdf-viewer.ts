import { Component, Input, OnInit, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-pdf-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pdf-viewer.html',
  styleUrl: './pdf-viewer.css'
})
export class PdfViewer implements OnInit {
  @Input() pdfUrl: string | null = null;
  @Input() filename: string = 'document.pdf';
  @ViewChild('pdfContainer', { static: true }) pdfContainer!: ElementRef;

  isLoading = false;
  error: string | null = null;
  currentPage = 1;
  totalPages = 0;
  scale = 1.0;

  ngOnInit() {
    if (this.pdfUrl) {
      this.loadPdf();
    }
  }

  ngOnChanges() {
    if (this.pdfUrl) {
      this.loadPdf();
    } else {
      this.clearViewer();
    }
  }

  private loadPdf() {
    this.isLoading = true;
    this.error = null;

    // For now, we'll use iframe for PDF display
    // In a production app, you might want to use PDF.js for more control
    const iframe = document.createElement('iframe');
    iframe.src = this.pdfUrl!;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';

    // Clear previous content
    this.pdfContainer.nativeElement.innerHTML = '';
    this.pdfContainer.nativeElement.appendChild(iframe);

    iframe.onload = () => {
      this.isLoading = false;
    };

    iframe.onerror = () => {
      this.error = 'Failed to load PDF';
      this.isLoading = false;
    };
  }

  private clearViewer() {
    if (this.pdfContainer?.nativeElement) {
      this.pdfContainer.nativeElement.innerHTML = `
        <div class="pdf-placeholder">
          <div class="placeholder-content">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14,2 14,8 20,8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10,9 9,9 8,9"></polyline>
            </svg>
            <h3>Your PDF will be displayed here</h3>
            <p>Upload a document to get started</p>
          </div>
        </div>
      `;
    }
  }

  zoomIn() {
    this.scale = Math.min(this.scale + 0.2, 3.0);
    this.updateScale();
  }

  zoomOut() {
    this.scale = Math.max(this.scale - 0.2, 0.5);
    this.updateScale();
  }

  resetZoom() {
    this.scale = 1.0;
    this.updateScale();
  }

  private updateScale() {
    const iframe = this.pdfContainer.nativeElement.querySelector('iframe');
    if (iframe) {
      iframe.style.transform = `scale(${this.scale})`;
      iframe.style.transformOrigin = 'top left';
    }
  }

  downloadPdf() {
    if (this.pdfUrl) {
      const link = document.createElement('a');
      link.href = this.pdfUrl;
      link.download = this.filename;
      link.click();
    }
  }

  // Helper method to access Math in template
  getMath() {
    return Math;
  }

  // Helper method for scale percentage
  getScalePercentage(): number {
    return Math.round(this.scale * 100);
  }
}