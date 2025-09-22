import { Component, OnInit, signal, OnDestroy } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { PdfViewer } from '../pdf-viewer/pdf-viewer';
import { chatHistoryData } from '../mock-data';

interface Message {
  role: 'user' | 'AI';
  content: string;
  timestamp: Date;
}

interface ChatSession {
  id: string;
  title: string;
  pdfFile?: string; // Add the optional pdfFile property
  chat: { user: string; AI: string }[];
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, PdfViewer, DatePipe],
  templateUrl: './chat.html',
  styleUrls: ['./chat.css'],
})
export class Chat implements OnInit, OnDestroy {
  // Component State
  currentChat = signal<ChatSession | null>(null);
  messages = signal<Message[]>([]);
  currentMessage = signal('');
  isLoading = signal(false);
  error = signal<string | null>(null);
  
  // UI State
  summaryWidth = signal(400);
  chatHeightVh = signal(40);
  isChatCollapsed = signal(false);
  isDragging = signal(false);

  private routeSub!: Subscription;

  // Mock data for the view
  pdfUrl = signal<string | null>(null); // Start with null
  document = signal<{ filename: string, title: string, document_type: string } | null>(null);
  summary = signal({ summary: 'This is a mock summary of the uploaded document, outlining key financial performance and strategic initiatives for the fiscal year.', key_points: ['Revenue increased by 15%', 'New market expansion in Asia', 'Successful launch of Product X'], complexity_score: 7 });
  suggestedQuestions = signal<string[]>([]);

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit() {
    this.routeSub = this.route.paramMap.subscribe(params => {
      const chatId = params.get('id');
      if (chatId) {
        const foundChat = chatHistoryData.find(chat => chat.id === chatId);
        if (foundChat) {
          this.currentChat.set(foundChat);
          this.messages.set([]);
          this.currentMessage.set('');
          this.error.set(null);
          this.suggestedQuestions.set(foundChat.chat.map(q => q.user));

          // ** NEW LOGIC TO UPDATE PDF **
          if (foundChat.pdfFile) {
            this.pdfUrl.set(foundChat.pdfFile);
            this.document.set({
              filename: foundChat.pdfFile,
              title: foundChat.title,
              document_type: 'PDF'
            });
          } else {
            // Fallback if a PDF is not specified in mock data
            this.pdfUrl.set(null);
            this.document.set(null);
          }

        } else {
          this.router.navigate(['/welcome']);
        }
      }
    });
  }
  
  // ... (rest of the file is unchanged) ...
  ngOnDestroy() {
    if (this.routeSub) {
      this.routeSub.unsubscribe();
    }
  }
  
  sendMessage() {
    this.useSuggestedQuestion(this.currentMessage().trim());
  }

  useSuggestedQuestion(question: string) {
    if (!question || !this.currentChat()) return;

    this.messages.update(msgs => [...msgs, { role: 'user', content: question, timestamp: new Date() }]);
    this.currentMessage.set('');
    this.isLoading.set(true);

    const mockResponse = this.currentChat()?.chat.find(
      qa => qa.user.toLowerCase() === question.toLowerCase()
    );

    setTimeout(() => {
      const aiContent = mockResponse ? mockResponse.AI : "Sorry, Bhaiya, I don't have a pre-recorded answer for that. Please try one of the suggested questions.";
      this.messages.update(msgs => [...msgs, { role: 'AI', content: aiContent, timestamp: new Date() }]);
      this.isLoading.set(false);
    }, 1500);
  }

  onInputChange(event: Event) {
    this.currentMessage.set((event.target as HTMLInputElement).value);
  }

  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  toggleChat() {
    this.isChatCollapsed.set(!this.isChatCollapsed());
  }
  
  startResize(event: MouseEvent, direction: 'width' | 'height') {
    // This is a placeholder for actual resize logic
    console.log('Start resizing', direction);
    this.isDragging.set(true);
  }
}