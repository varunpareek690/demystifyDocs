import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

export interface UserProfile {
  name: string;
  picture: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  currentUser = signal<UserProfile | null>(null);

  constructor(private router: Router) { }

  saveUserAndToken(token: string) {
    localStorage.setItem('authToken', token);
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      this.currentUser.set({
        name: payload.name,
        picture: payload.picture
      });
    } catch (e) {
      console.error("Could not decode token", e);
      this.logout();
    }
  }

  logout() {
    localStorage.removeItem('authToken');
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem('authToken');
  }
}