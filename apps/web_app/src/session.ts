import type { AdultConsentStatus, WebSession } from './api';

const SESSION_STORAGE_KEY = 'adultgen.web.session';
const ADULT_CONSENT_KEY = 'adultgen.web.adult_consent';

export function loadWebSession(): WebSession | null {
  return loadJson<WebSession>(SESSION_STORAGE_KEY);
}

export function saveWebSession(session: WebSession): void {
  window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function clearWebSession(): void {
  window.localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function loadAdultConsentStatus(): AdultConsentStatus | null {
  return loadJson<AdultConsentStatus>(ADULT_CONSENT_KEY);
}

export function saveAdultConsentStatus(status: AdultConsentStatus): void {
  window.localStorage.setItem(ADULT_CONSENT_KEY, JSON.stringify(status));
}

function loadJson<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}
