import { Component } from '@angular/core';
import { Location } from '@angular/common'; // 1. Import Location

@Component({
  selector: 'app-feature-placeholder',
  standalone: true,
  imports: [],
  templateUrl: './feature-placeholder.html',
  styleUrl: './feature-placeholder.css'
})
export class FeaturePlaceholder {

  // 2. Inject Location in the constructor
  constructor(private location: Location) {}

  // 3. Create a function to go back
  goBack(): void {
    this.location.back();
  }
}