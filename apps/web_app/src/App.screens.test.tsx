import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { App } from './App';
import { AdminPanel } from './AdminPanel';
import { webAppRoutes } from './routes';
import { saveAdultConsentStatus, saveWebSession } from './session';
import type { WebSession } from './api';

const mockSession: WebSession = {
  access_token: 'test-token',
  token_type: 'bearer',
  user_id: 'user-1',
  telegram_user_id: -1,
  email: 'creator@example.com',
  display_name: 'AdultGen creator',
  is_blocked: false,
  capabilities: {
    can_generate: true,
    can_publish_profile: true,
    can_publish_feed: true,
    can_use_payments: true,
  },
};

function jsonResponse(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  window.localStorage.clear();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/generations')) return jsonResponse({ items: [] });
      if (url.includes('/billing/packages')) return jsonResponse({ items: [] });
      if (url.includes('/wallet/me')) {
        return jsonResponse({
          currency: 'credits',
          total_available: 0,
          total_reserved: 0,
          total_balance: 0,
          buckets: [],
        });
      }
      return jsonResponse({ items: [] });
    }),
  );
  saveWebSession(mockSession);
  saveAdultConsentStatus({ accepted: true, policy_version: 'test', accepted_at: '2026-01-01T00:00:00Z' });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  window.localStorage.clear();
  window.history.replaceState(null, '', '/');
});

describe('App route screens', () => {
  it.each(webAppRoutes.map((route) => [route.id, route.path, route.title]))(
    'renders %s route screen without replacing it with a broken state',
    (_routeId, path, title) => {
      window.history.replaceState(null, '', path);

      render(<App />);

      expect(screen.getByRole('heading', { level: 2, name: title })).toBeTruthy();
      expect(screen.getByLabelText('Route selector')).toBeTruthy();
      expect(screen.queryByText('Shell extraction contract')).toBeNull();
    },
  );

  it('renders real working cards for previously placeholder routes', () => {
    window.history.replaceState(null, '', '/projects');
    const { unmount } = render(<App />);
    expect(screen.getByText('Проекты и сцены')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Открыть Studio' })).toBeTruthy();
    unmount();

    window.history.replaceState(null, '', '/avatars');
    render(<App />);
    expect(screen.getByText('Аватары и visual identity')).toBeTruthy();
    expect(screen.getByLabelText('Reference upload')).toBeTruthy();
  });
});

describe('AdminPanel route', () => {
  it('renders locked admin state without token', () => {
    window.localStorage.clear();

    render(<AdminPanel />);

    expect(screen.getByRole('heading', { name: 'Control Room' })).toBeTruthy();
    expect(screen.getByText('Нужен ADMIN_API_TOKEN')).toBeTruthy();
  });
});
