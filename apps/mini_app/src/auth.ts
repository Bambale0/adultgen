import { useEffect, useMemo, useState } from 'react';

import { getBotUsername, getCoreApiBaseUrl } from './env';
import { getTelegramLaunchData } from './telegram';

export type UserCapabilities = {
  can_generate: boolean;
  can_publish_profile: boolean;
  can_publish_feed: boolean;
  can_use_payments: boolean;
};

export type AuthenticatedSession = {
  access_token: string;
  user_id: string;
  telegram_user_id: number;
  is_blocked: boolean;
  capabilities: UserCapabilities;
};

export type AuthState =
  | { status: 'loading' }
  | { status: 'authenticated'; session: AuthenticatedSession }
  | { status: 'missing-telegram' }
  | { status: 'error'; message: string };

export async function authenticateTelegramMiniApp(
  initData: string,
  startPayload: string | null,
): Promise<AuthenticatedSession> {
  const response = await fetch(`${getCoreApiBaseUrl()}/auth/telegram-mini-app`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      bot_username: getBotUsername(),
      init_data: initData,
      start_payload: startPayload,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === 'string' ? body.detail : 'Mini App auth failed.';
    throw new Error(detail);
  }

  return (await response.json()) as AuthenticatedSession;
}

export function useTelegramMiniAppAuth(): AuthState {
  const launchData = useMemo(() => getTelegramLaunchData(), []);
  const [state, setState] = useState<AuthState>({ status: 'loading' });

  useEffect(() => {
    let cancelled = false;

    async function runAuth() {
      if (!launchData.isTelegramEnvironment) {
        setState({ status: 'missing-telegram' });
        return;
      }

      try {
        const session = await authenticateTelegramMiniApp(
          launchData.initData,
          launchData.startParam,
        );
        if (!cancelled) {
          localStorage.setItem('adultgen.accessToken', session.access_token);
          setState({ status: 'authenticated', session });
        }
      } catch (error) {
        if (!cancelled) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'Mini App auth failed.',
          });
        }
      }
    }

    void runAuth();
    return () => {
      cancelled = true;
    };
  }, [launchData]);

  return state;
}
