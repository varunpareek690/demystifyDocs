import { Component, OnInit, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';

declare global {
  interface Window {
    google: any;
  }
}

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auth.html',
  styleUrl: './auth.css'
})
export class Auth implements OnInit, AfterViewInit {
  private apiUrl = 'http://localhost:8080/api/v1'; // Your backend IP

  constructor(
    private http: HttpClient,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit() {
    this.initializeGoogleAuth();
  }

  ngAfterViewInit() {
    setTimeout(() => this.renderGoogleButton(), 100);
  }

  async initializeGoogleAuth() {
    try {
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
          { theme: "outline", size: "large", width: "300" }
        );
      }
    }
  }

  handleCredentialResponse(response: any) {
    if (response.credential) {
      this.loginWithGoogle(response.credential);
    }
  }

  async loginWithGoogle(idToken: string) {
    try {
      const result: any = await this.http.post(`${this.apiUrl}/auth/google`, {
        id_token: idToken
      }).toPromise();

      console.log('Login successful:', result);
      
      if (result && result.data && result.data.access_token) {
        this.authService.saveUserAndToken(result.data.access_token);
        this.router.navigate(['/welcome']);
      } else {
         console.error('Login failed: No access_token in response');
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  }
}