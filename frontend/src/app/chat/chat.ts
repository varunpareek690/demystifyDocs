import { Component, HostListener, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { PdfViewer } from '../pdf-viewer/pdf-viewer';
import { ChatService, ChatMessage, ChatSessionWithMessages } from '../services/chat.service';
import { DocumentService, Document, DocumentSummary } from '../services/document.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, PdfViewer],
  templateUrl: './chat.html',
  styleUrl: './chat.css'
})
export class Chat implements OnInit {
  // --- State for Chat Overlay ---
  isChatCollapsed = signal(false);
  
  // --- State for Resizing ---
  summaryWidth = signal(280);
  chatHeightVh = signal(25);
  isResizingWidth = false;
  isResizingHeight = false;
  isDragging = signal(false);

  // --- Document and Chat State ---
  document = signal<Document | null>(null);
  summary = signal<DocumentSummary | null>(null);
  suggestedQuestions = signal<string[]>([]);
  currentSessionId = signal<string | null>(null);
  messages = signal<ChatMessage[]>([]);
  
  // --- PDF Viewer State ---
  pdfUrl = signal<string | null>(null);
  
  // --- Input and Loading State ---
  currentMessage = signal('');
  isLoading = signal(false);
  error = signal<string | null>(null);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private chatService: ChatService,
    private documentService: DocumentService
  ) {}

  ngOnInit() {
    // Get session ID from route if available
    const sessionId = this.route.snapshot.params['sessionId'];
    if (sessionId) {
      this.currentSessionId.set(sessionId);
      this.loadChatSession(sessionId);
    }

    // Get data from navigation state (from upload)
    const navigationState = history.state;
    if (navigationState?.document) {
      this.document.set(navigationState.document);
      if (navigationState.summary) {
        this.summary.set(navigationState.summary);
      }
      if (navigationState.suggestedQuestions) {
        this.suggestedQuestions.set(navigationState.suggestedQuestions);
      }
      
      // Get PDF URL if available
      if (navigationState.document.id) {
        this.requestPdfUrl(navigationState.document.id);
      }
    }
  }

  async loadChatSession(sessionId: string) {
    this.isLoading.set(true);
    this.error.set(null);
    
    try {
      this.chatService.getChatSession(sessionId).subscribe({
        next: (response) => {
          if (response.success) {
            const sessionData = response.data.session;
            this.messages.set(sessionData.messages);
            this.suggestedQuestions.set(response.data.suggested_questions);
            
            // Load document data
            this.loadDocumentData(sessionData.session.document_id);
          } else {
            this.error.set(response.message || 'Failed to load chat session');
          }
        },
        error: (error) => {
          this.error.set('Failed to load chat session');
          console.error('Error loading chat session:', error);
        },
        complete: () => {
          this.isLoading.set(false);
        }
      });
    } catch (error) {
      this.error.set('Failed to load chat session');
      console.error('Error loading chat session:', error);
      this.isLoading.set(false);
    }
  }

  private loadDocumentData(documentId: string) {
    this.documentService.getDocumentWithSummary(documentId).subscribe({
      next: (response) => {
        if (response.success) {
          this.document.set(response.data.document);
          this.summary.set(response.data.summary);
          
          // Get PDF URL
          if (response.data.document.id) {
            this.requestPdfUrl(response.data.document.id);
          }
        }
      },
      error: (error) => {
        console.error('Error loading document data:', error);
      }
    });
  }

  private requestPdfUrl(documentId: string) {
    this.documentService.getDocumentDownloadUrl(documentId).subscribe({
      next: (response) => {
        if (response.success) {
          this.pdfUrl.set(response.data.download_url);
        }
      },
      error: (error) => {
        console.error('Error getting PDF URL:', error);
        // Don't show error to user for PDF loading failure
      }
    });
  }

  async sendMessage() {
    const message = this.currentMessage().trim();
    if (!message || this.isLoading()) return;

    const sessionId = this.currentSessionId();
    if (!sessionId) {
      this.error.set('No active chat session');
      return;
    }

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `temp_user_${Date.now()}`,
      chat_session_id: sessionId,
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    this.messages.set([...this.messages(), userMessage]);
    this.currentMessage.set('');
    this.isLoading.set(true);

    try {
      this.chatService.sendMessage(sessionId, message).subscribe({
        next: (response) => {
          if (response.success) {
            // Replace the temporary user message and add AI response
            const currentMessages = this.messages();
            const filteredMessages = currentMessages.filter(msg => msg.id !== userMessage.id);
            
            this.messages.set([
              ...filteredMessages,
              response.data.user_message,
              response.data.ai_message
            ]);
          } else {
            this.error.set(response.message || 'Failed to send message');
          }
        },
        error: (error) => {
          this.error.set('Failed to send message');
          console.error('Error sending message:', error);
          
          // Remove the temporary message on error
          const currentMessages = this.messages();
          this.messages.set(currentMessages.filter(msg => msg.id !== userMessage.id));
        },
        complete: () => {
          this.isLoading.set(false);
        }
      });
    } catch (error) {
      this.error.set('Failed to send message');
      console.error('Error sending message:', error);
      this.isLoading.set(false);
      
      // Remove the temporary message on error
      const currentMessages = this.messages();
      this.messages.set(currentMessages.filter(msg => msg.id !== userMessage.id));
    }
  }

  useSuggestedQuestion(question: string) {
    this.currentMessage.set(question);
  }

  clearError() {
    this.error.set(null);
  }

  toggleChat() {
    this.isChatCollapsed.set(!this.isChatCollapsed());
  }

  // --- Logic for Resizing ---
  startResize(event: MouseEvent, direction: 'width' | 'height') {
    if (direction === 'width') {
      this.isResizingWidth = true;
    } else {
      this.isResizingHeight = true;
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

  // Handle input events
  onInputChange(event: Event) {
    const target = event.target as HTMLInputElement;
    this.currentMessage.set(target.value);
  }

  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}