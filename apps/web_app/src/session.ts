import type { AdultConsentStatus, WebSession } from './api';

const SESSION_KEY = 'adultgen.web-session.v1';
const CONSENT_KEY = 'adultgen.adult-consent.v1';

export function loadWebSession(): WebSession | null {
  return read<WebSession>(SESSION_KEY);
}

export function saveWebSession(session: WebSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearWebSession(): void {
  window.localStorage.removeItem(SESSION_KEY);
  window.localStorage.removeItem(CONSENT_KEY);
}

export function loadAdultConsentStatus(): AdultConsentStatus | null {
  return read<AdultConsentStatus>(CONSENT_KEY);
}

export function saveAdultConsentStatus(status: AdultConsentStatus): void {
  window.localStorage.setItem(CONSENT_KEY, JSON.stringify(status));
}

function read<T>(key: string): T | null {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : null;
  } catch {
    window.localStorage.removeItem(key);
    return null;
  }
}
