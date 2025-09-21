import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Document {
  id: string;
  title: string;
  content: string;
  filename?: string;
  blob_path?: string;
  gcs_url?: string;
  file_size?: number;
  file_type?: string;
  content_type?: string;
  document_type: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  document_id: string;
  summary: string;
  key_points: string[];
  highlights: any[];
  complexity_score: number;
  important_dates: string[];
  obligations: string[];
  rights: string[];
  risks: string[];
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private apiUrl = 'http://localhost:8080/api/v1';
  
  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Content-Type': 'application/json',
    });
  }

  getDocuments(includeSummaries: boolean = false, limit: number = 50): Observable<ApiResponse<{
    documents: Document[];
    count: number;
    documents_with_summaries?: any[];
  }>> {
    const params = new URLSearchParams({
      include_summaries: includeSummaries.toString(),
      limit: limit.toString()
    });

    return this.http.get<ApiResponse<{
      documents: Document[];
      count: number;
      documents_with_summaries?: any[];
    }>>(
      `${this.apiUrl}/documents/?${params}`,
      { headers: this.getHeaders() }
    );
  }

  // Get a specific document
  getDocument(documentId: string): Observable<ApiResponse<{ document: Document }>> {
    return this.http.get<ApiResponse<{ document: Document }>>(
      `${this.apiUrl}/documents/${documentId}`,
      { headers: this.getHeaders() }
    );
  }

  // Get document with summary
  getDocumentWithSummary(documentId: string, regenerate: boolean = false): Observable<ApiResponse<{
    document: Document;
    summary: DocumentSummary;
    chat_sessions: any[];
    has_chat_sessions: boolean;
  }>> {
    const params = regenerate ? '?regenerate=true' : '';
    
    return this.http.get<ApiResponse<{
      document: Document;
      summary: DocumentSummary;
      chat_sessions: any[];
      has_chat_sessions: boolean;
    }>>(
      `${this.apiUrl}/documents/${documentId}/with-summary${params}`,
      { headers: this.getHeaders() }
    );
  }

  // Get download URL for document
  getDocumentDownloadUrl(documentId: string, expirationMinutes: number = 60): Observable<ApiResponse<{
    download_url: string;
    filename: string;
    file_size: number;
    expires_in_minutes: number;
  }>> {
    return this.http.get<ApiResponse<{
      download_url: string;
      filename: string;
      file_size: number;
      expires_in_minutes: number;
    }>>(
      `${this.apiUrl}/documents/${documentId}/download?expiration_minutes=${expirationMinutes}`,
      { headers: this.getHeaders() }
    );
  }

  // Regenerate document summary
  regenerateSummary(documentId: string): Observable<ApiResponse<{ summary: DocumentSummary }>> {
    return this.http.post<ApiResponse<{ summary: DocumentSummary }>>(
      `${this.apiUrl}/documents/${documentId}/regenerate-summary`,
      {},
      { headers: this.getHeaders() }
    );
  }

  // Delete document
  deleteDocument(documentId: string): Observable<ApiResponse<{ document_id: string }>> {
    return this.http.delete<ApiResponse<{ document_id: string }>>(
      `${this.apiUrl}/documents/${documentId}`,
      { headers: this.getHeaders() }
    );
  }

  // Upload text document
  uploadTextDocument(title: string, content: string, documentType: string = 'legal', autoCreateChat: boolean = true): Observable<ApiResponse<{
    document: Document;
    summary?: DocumentSummary;
    chat_session?: any;
    suggested_questions?: string[];
  }>> {
    const payload = {
      title,
      content,
      document_type: documentType
    };

    const params = autoCreateChat ? '?auto_create_chat=true' : '';

    return this.http.post<ApiResponse<{
      document: Document;
      summary?: DocumentSummary;
      chat_session?: any;
      suggested_questions?: string[];
    }>>(
      `${this.apiUrl}/documents/text${params}`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Get detailed document history
  getDocumentHistory(includeSummaries: boolean = false, includeChatInfo: boolean = true, limit: number = 20): Observable<ApiResponse<{
    history: any[];
    total_documents: number;
    showing_limit: number;
  }>> {
    const params = new URLSearchParams({
      include_summaries: includeSummaries.toString(),
      include_chat_info: includeChatInfo.toString(),
      limit: limit.toString()
    });

    return this.http.get<ApiResponse<{
      history: any[];
      total_documents: number;
      showing_limit: number;
    }>>(
      `${this.apiUrl}/documents/history/detailed?${params}`,
      { headers: this.getHeaders() }
    );
  }
}