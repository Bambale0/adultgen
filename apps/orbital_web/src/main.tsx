import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './styles.css';

const SESSION_KEY = 'adultgen.orbital.session';
const CONSENT_KEY = 'adultgen.orbital.consent';
const session = localStorage.getItem(SESSION_KEY);
const requiresSession = ['/studio', '/missions', '/profile', '/billing'].includes(window.location.pathname);
const requiresAdultConsent = ['/studio', '/missions', '/profile'].includes(window.location.pathname);
let accepted = false;

try {
  accepted = Boolean(JSON.parse(localStorage.getItem(CONSENT_KEY) || 'null')?.accepted);
} catch {
  accepted = false;
}

if ((requiresSession && !session) || (requiresAdultConsent && !accepted)) {
  window.history.replaceState({ route: 'feed' }, '', '/');
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
