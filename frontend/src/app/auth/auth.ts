import { Component, OnInit, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

declare global {
  interface Window {
    google: any;
  }
}

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="auth-container">
      <div class="auth-card">
        <h2>Sign in to Your App</h2>
        <p>Use your Google account to continue</p>
        
        <div id="g_id_onload"></div>
        <div id="g_id_signin"></div>
        
        <button class="google-btn" (click)="signInWithGoogle()" type="button">
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </div>
  `,
  styles: [`
    .auth-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;
      padding: 20px;
    }
    
    .auth-card {
      background: white;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
      text-align: center;
      max-width: 400px;
      width: 100%;
    }
    
    .google-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      background: white;
      border: 1px solid #dadce0;
      border-radius: 4px;
      padding: 12px 24px;
      font-size: 14px;
      cursor: pointer;
      width: 100%;
      margin-top: 1rem;
    }
    
    .google-btn:hover {
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
  `]
})
export class Auth implements OnInit, AfterViewInit {
  private apiUrl = 'http://10.238.216.143:8080/api/v1'; // Remember to replace this with your actual backend IP
  
  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.initializeGoogleAuth();
  }

  ngAfterViewInit() {
    // Render the official Google button after the view is initialized
    setTimeout(() => this.renderGoogleButton(), 100);
  }

  async initializeGoogleAuth() {
    try {
      // Get the Google Client ID dynamically from your backend
      const config: any = await this.http.get(`${this.apiUrl}/auth/google/config`).toPromise();
      
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: config.data.client_id,
          callback: this.handleCredentialResponse.bind(this)
        });
      }
    } catch (error) {
      console.error('Failed to initialize Google Auth:', error);
    }
  }

  renderGoogleButton() {
    if (window.google && window.google.accounts) {
      const googleButtonElement = document.getElementById("g_id_signin");
      if (googleButtonElement) {
        window.google.accounts.id.renderButton(
          googleButtonElement,
          {
            type: "standard",
            shape: "rectangular", 
            theme: "outline",
            text: "signin_with",
            size: "large"
          }
        );
      }
    }
  }

  handleCredentialResponse(response: any) {
    if (response.credential) {
      // This is the ID token from Google
      this.loginWithGoogle(response.credential);
    }
  }

  async loginWithGoogle(idToken: string) {
    try {
      // Send the Google ID token to your backend for verification
      const result: any = await this.http.post(`${this.apiUrl}/auth/google`, { 
        id_token: idToken 
      }).toPromise();
      
      console.log('Login successful:', result);
      
      // After successful login, your backend should return your own app's token.
      // You would then save it and redirect the user.
      // Example:
      // localStorage.setItem('authToken', result.data.access_token);
      // window.location.href = '/welcome';
      
    } catch (error) {
      console.error('Login failed:', error);
    }
  }

  // This is a fallback to trigger the pop-up if the button doesn't render
  signInWithGoogle() {
    if (window.google && window.google.accounts) {
      window.google.accounts.id.prompt();
    }
  }
}