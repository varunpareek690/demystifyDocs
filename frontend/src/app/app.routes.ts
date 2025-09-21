import { Routes } from '@angular/router';
import { Welcome } from './welcome/welcome';
import { Chat } from './chat/chat';
import { FeaturePlaceholder } from './feature-placeholder/feature-placeholder'; 
import { Auth } from './auth/auth';

export const routes: Routes = [
  { path: '', redirectTo: '/login', pathMatch: 'full' },
  { path: 'login', component: Auth },
  { path: 'welcome', component: Welcome },
  { path: 'chat', component: Chat },
  { path: 'feature-in-progress', component: FeaturePlaceholder }, 
];