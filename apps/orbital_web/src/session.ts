import type { AdultConsentStatus, WebSession } from './api';

const SESSION_KEY = 'adultgen.orbital.session';
const CONSENT_KEY = 'adultgen.orbital.consent';

function read<T>(key: string): T | null {
  try {
    const value = localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : null;
  } catch {
    return null;
  }
}

export const sessionStore = {
  session: () => read<WebSession>(SESSION_KEY),
  consent: () => read<AdultConsentStatus>(CONSENT_KEY),
  saveSession: (session: WebSession) => localStorage.setItem(SESSION_KEY, JSON.stringify(session)),
  saveConsent: (consent: AdultConsentStatus) => localStorage.setItem(CONSENT_KEY, JSON.stringify(consent)),
  clear: () => {
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(CONSENT_KEY);
  },
};
