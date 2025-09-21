import { Component } from '@angular/core';
import { Router } from '@angular/router'; // 1. Import the Router

@Component({
  selector: 'app-welcome',
  standalone: true,
  imports: [],
  templateUrl: './welcome.html',
  styleUrl: './welcome.css'
})
export class Welcome {

  // 2. Inject the Router in the constructor
  constructor(private router: Router) {}

  // 3. Create the function for our button
  navigateToChat(): void {
    // We will make this more advanced later (e.g., only navigate after a file is uploaded)
    this.router.navigate(['/chat']);
  }

}