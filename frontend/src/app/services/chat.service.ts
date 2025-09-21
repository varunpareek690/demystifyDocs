import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ChatSession {
  id: string;
  title: string;
  document_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  is_active: boolean;
}

export interface ChatMessage {
  id: string;
  chat_session_id: string;
  role: 'user' | 'ai' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatSessionWithMessages {
  session: ChatSession;
  messages: ChatMessage[];
  document_title: string;
  document_summary?: string;
}

export interface SendMessageRequest {
  message: string;
}

export interface SendMessageResponse {
  success: boolean;
  message: string;
  data: {
    user_message: ChatMessage;
    ai_message: ChatMessage;
    session_updated: ChatSession;
    message_count: number;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private apiUrl = 'http://localhost:8000/api/v1'; // Adjust to your backend URL
  
  constructor(private http: HttpClient) {}

  private getHeaders(): HttpHeaders {
    // Add authentication headers here when you implement auth
    return new HttpHeaders({
      'Content-Type': 'application/json',
      // 'Authorization': `Bearer ${token}` // Add when auth is implemented
    });
  }

  // Create a new chat session
  createChatSession(documentId: string, title?: string): Observable<ApiResponse<{ session: ChatSession; suggested_questions: string[] }>> {
    const payload = {
      document_id: documentId,
      title: title
    };

    return this.http.post<ApiResponse<{ session: ChatSession; suggested_questions: string[] }>>(
      `${this.apiUrl}/chat/sessions`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Get a chat session with messages
  getChatSession(sessionId: string, includeMessages: boolean = true, messageLimit: number = 50): Observable<ApiResponse<{
    session: ChatSessionWithMessages;
    suggested_questions: string[];
    message_count: number;
    user_message_count: number;
  }>> {
    const params = new URLSearchParams({
      include_messages: includeMessages.toString(),
      message_limit: messageLimit.toString()
    });

    return this.http.get<ApiResponse<{
      session: ChatSessionWithMessages;
      suggested_questions: string[];
      message_count: number;
      user_message_count: number;
    }>>(
      `${this.apiUrl}/chat/sessions/${sessionId}?${params}`,
      { headers: this.getHeaders() }
    );
  }

  // Send a message in a chat session
  sendMessage(sessionId: string, message: string): Observable<SendMessageResponse> {
    const payload: SendMessageRequest = { message };

    return this.http.post<SendMessageResponse>(
      `${this.apiUrl}/chat/sessions/${sessionId}/messages`,
      payload,
      { headers: this.getHeaders() }
    );
  }

  // Get user's chat history
  getChatHistory(limit: number = 50): Observable<ApiResponse<{
    sessions: any[];
    total_sessions: number;
    showing_limit: number;
  }>> {
    return this.http.get<ApiResponse<{
      sessions: any[];
      total_sessions: number;
      showing_limit: number;
    }>>(
      `${this.apiUrl}/chat/history?limit=${limit}`,
      { headers: this.getHeaders() }
    );
  }

  // Get suggested questions for a session
  getSuggestedQuestions(sessionId: string): Observable<ApiResponse<{
    suggested_questions: string[];
    session_id: string;
  }>> {
    return this.http.get<ApiResponse<{
      suggested_questions: string[];
      session_id: string;
    }>>(
      `${this.apiUrl}/chat/sessions/${sessionId}/suggested-questions`,
      { headers: this.getHeaders() }
    );
  }

  // Delete a chat session
  deleteChatSession(sessionId: string): Observable<ApiResponse<{
    session_id: string;
    deleted_messages: number;
    session_title: string;
  }>> {
    return this.http.delete<ApiResponse<{
      session_id: string;
      deleted_messages: number;
      session_title: string;
    }>>(
      `${this.apiUrl}/chat/sessions/${sessionId}`,
      { headers: this.getHeaders() }
    );
  }

  // Export chat session
  exportChatSession(sessionId: string, format: 'json' | 'txt' | 'markdown' = 'json'): Observable<ApiResponse<{
    export_data: string;
    format: string;
    session_id: string;
    message_count: number;
  }>> {
    return this.http.get<ApiResponse<{
      export_data: string;
      format: string;
      session_id: string;
      message_count: number;
    }>>(
      `${this.apiUrl}/chat/sessions/${sessionId}/export?format=${format}`,
      { headers: this.getHeaders() }
    );
  }

  // Get chat statistics
  getChatStats(): Observable<ApiResponse<{
    total_sessions: number;
    total_messages: number;
    active_sessions: number;
    recent_activity_7days: number;
    average_messages_per_session: number;
    most_active_session?: any;
  }>> {
    return this.http.get<ApiResponse<{
      total_sessions: number;
      total_messages: number;
      active_sessions: number;
      recent_activity_7days: number;
      average_messages_per_session: number;
      most_active_session?: any;
    }>>(
      `${this.apiUrl}/chat/stats`,
      { headers: this.getHeaders() }
    );
  }
}