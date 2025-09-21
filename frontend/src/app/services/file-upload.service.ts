import { Injectable } from '@angular/core';
import { HttpClient, HttpEventType, HttpRequest } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map } from 'rxjs/operators';

export interface UploadProgress {
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  message?: string;
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  data: {
    document: any;
    summary: any;
    chat_session: any;
    suggested_questions: string[];
    file_info: any;
  };
}

@Injectable({
  providedIn: 'root'
})
export class FileUploadService {
  private apiUrl = 'http://localhost:8080/api/v1';
  private uploadProgress$ = new BehaviorSubject<UploadProgress>({ progress: 0, status: 'uploading' });

  constructor(private http: HttpClient) {}

  uploadFile(file: File, customTitle?: string): Observable<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (customTitle) {
      formData.append('title', customTitle);
    }

    const request = new HttpRequest('POST', `${this.apiUrl}/documents/upload`, formData, {
      reportProgress: true
    });

    return this.http.request(request).pipe(
      map(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            const progress = Math.round(100 * event.loaded / (event.total || 1));
            this.uploadProgress$.next({
              progress,
              status: progress < 100 ? 'uploading' : 'processing',
              message: progress < 100 ? 'Uploading file...' : 'Processing document...'
            });
            return null;

          case HttpEventType.Response:
            this.uploadProgress$.next({
              progress: 100,
              status: 'completed',
              message: 'Document processed successfully!'
            });
            return event.body as DocumentUploadResponse;

          default:
            return null;
        }
      })
    ).pipe(
      // Filter out null values (progress events)
      map(response => response as DocumentUploadResponse)
    );
  }

  getUploadProgress(): Observable<UploadProgress> {
    return this.uploadProgress$.asObservable();
  }

  resetProgress(): void {
    this.uploadProgress$.next({ progress: 0, status: 'uploading' });
  }
}