import { Routes } from '@angular/router';
import { Welcome } from './welcome/welcome';
import { Chat } from './chat/chat';
import { FeaturePlaceholder } from './feature-placeholder/feature-placeholder';
import { Auth } from './auth/auth';
import { authGuard } from './auth-guard';
import { AuthCallback } from './auth-callback/auth-callback';

export const routes: Routes = [
  { path: '', redirectTo: '/welcome', pathMatch: 'full' },
  { path: 'login', component: Auth },
  { path: 'auth/callback', component: AuthCallback },
  { path: 'welcome', component: Welcome, canActivate: [authGuard] },
  // Updated route to handle dynamic chat IDs
  { path: 'chat/:id', component: Chat, canActivate: [authGuard] }, 
  { path: 'feature-in-progress', component: FeaturePlaceholder, canActivate: [authGuard] },
  // Fallback if user goes to /chat without an ID
  { path: 'chat', redirectTo: '/welcome', pathMatch: 'full' },
];