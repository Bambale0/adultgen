export type SubscriptionPlan = {
  code: string;
  title: string;
  credits_per_period: number;
  amount_minor: number;
  amount_major: string;
  currency: string;
  period_days: number;
  rollover_policy: string;
  description: string;
  is_popular: boolean;
};

export type Subscription = {
  id: string;
  plan_code: string;
  status: string;
  provider: string | null;
  provider_subscription_id: string | null;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  cancelled_at: string | null;
  last_granted_at: string | null;
};

export type SubscriptionActivationResponse = {
  subscription: Subscription;
  plan: SubscriptionPlan;
  granted_now: boolean;
  grant_id: string | null;
  credits_granted: number;
};

const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export async function fetchSubscriptionPlans(): Promise<{ items: SubscriptionPlan[] }> {
  return request<{ items: SubscriptionPlan[] }>('/subscriptions/plans');
}

export async function fetchMySubscription(accessToken: string): Promise<Subscription | null> {
  return request<Subscription | null>('/subscriptions/me', { accessToken });
}

export async function activateSubscription(
  accessToken: string,
  planCode: string,
): Promise<SubscriptionActivationResponse> {
  return request<SubscriptionActivationResponse>('/subscriptions/activate', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ plan_code: planCode, provider: 'manual_mvp' }),
  });
}

export async function cancelSubscriptionAtPeriodEnd(accessToken: string): Promise<Subscription> {
  return request<Subscription>('/subscriptions/me/cancel-at-period-end', {
    method: 'POST',
    accessToken,
  });
}

async function request<T = unknown>(
  path: string,
  options: RequestInit & { accessToken?: string } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (options.accessToken) headers.set('Authorization', `Bearer ${options.accessToken}`);

  const response = await fetch(`${CORE_API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const fallback = `${response.status} ${response.statusText}`;
    let detail = fallback;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : fallback;
    } catch {
      detail = fallback;
    }
    throw new Error(detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
