import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-auth-callback',
  standalone: true,
  imports: [],
  template: '<p class="loading-text">Logging you in...</p>',
  styles: `
    .loading-text {
      color: #fff;
      font-size: 1.5rem;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
    }
  `
})
export class AuthCallback implements OnInit {

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    // This looks for a query parameter named 'token' in the URL
    this.route.queryParams.subscribe(params => {
      const token = params['token'];

      if (token) {
        // We found a token! Save it to localStorage.
        console.log('Token received:', token);
        localStorage.setItem('authToken', token);
        
        // Redirect to the main welcome page
        this.router.navigate(['/welcome']);
      } else {
        // No token found, something went wrong. Redirect to login.
        console.error('Authentication failed: No token received.');
        this.router.navigate(['/login']);
      }
    });
  }
}