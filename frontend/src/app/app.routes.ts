import { Routes } from '@angular/router';
import { Welcome } from './welcome/welcome';
import { Chat } from './chat/chat';
import { FeaturePlaceholder } from './feature-placeholder/feature-placeholder'; 
import { Auth } from './auth/auth';
import { authGuard } from './auth-guard'; 

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: Auth },

  { path: 'welcome', component: Welcome, canActivate: [authGuard] },
  { path: 'chat', component: Chat, canActivate: [authGuard] },
  { path: 'feature-in-progress', component: FeaturePlaceholder, canActivate: [authGuard] },
];