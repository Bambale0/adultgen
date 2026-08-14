const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export type CapabilitySet = {
  can_generate: boolean;
  can_publish_profile: boolean;
  can_publish_feed: boolean;
  can_use_payments: boolean;
};

export type WebSession = {
  access_token: string;
  token_type: string;
  user_id: string;
  telegram_user_id: number;
  provider?: 'google' | 'telegram';
  email?: string | null;
  display_name: string;
  is_blocked: boolean;
  capabilities: CapabilitySet;
};

export type TelegramLoginPayload = {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
};

export type AdultConsentStatus = {
  accepted: boolean;
  policy_version: string;
  accepted_at: string | null;
};

export type WalletBalance = {
  currency: string;
  total_available: number;
  total_reserved: number;
  total_balance: number;
  buckets: Array<{ bucket: string; available: number; reserved: number }>;
};

export type WalletBucketBalance = WalletBalance['buckets'][number];

export type CreditPackage = {
  code: string;
  title: string;
  credits: number;
  amount_minor: number;
  amount_major: string;
  currency: string;
  description: string;
  is_popular: boolean;
};

export type PaymentOrder = {
  id: string;
  provider: string;
  package_code: string;
  amount_minor: number;
  currency: string;
  credits_amount: number;
  status: string;
  expires_at: string;
  paid_at: string | null;
  checkout_url?: string | null;
  provider_checkout_url?: string | null;
};

export type GenerationResultAsset = {
  asset_id: string;
  role: string;
  media_url: string;
  is_external: boolean;
};

export type GenerationTask = {
  id: string;
  status: string;
  provider: string;
  model_code: string;
  operation: string;
  reserved_credits: number;
  charged_credits: number;
  error_message?: string | null;
  results: GenerationResultAsset[];
};

export type GenerationListResponse = { items: GenerationTask[] };

export type FeedItem = {
  id: string;
  title: string | null;
  description: string | null;
  media_url: string;
  preview_url: string;
  blur_preview_url: string | null;
  is_explicit: boolean;
  blur_required: boolean;
  allow_remix: boolean;
  status: string;
};

export type UserProfile = {
  id: string;
  public_id: string;
  display_name: string | null;
  bio: string | null;
  visibility: 'public' | 'private';
};

export async function authenticateGoogle(credential: string): Promise<WebSession> {
  return request<WebSession>('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ credential }),
  });
}

export async function authenticateTelegramLogin(payload: TelegramLoginPayload): Promise<WebSession> {
  return request<WebSession>('/auth/telegram-login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function authenticateTelegramMiniApp(
  botUsername: string,
  initData: string,
): Promise<WebSession> {
  const result = await request<Omit<WebSession, 'display_name'> & { display_name?: string }>(
    '/auth/telegram-mini-app',
    {
      method: 'POST',
      body: JSON.stringify({ bot_username: botUsername, init_data: initData }),
    },
  );
  return { ...result, display_name: result.display_name || 'Telegram creator', provider: 'telegram' };
}

export function fetchAdultConsentStatus(accessToken: string): Promise<AdultConsentStatus> {
  return request('/adult-consent', { accessToken });
}

export function acceptAdultConsent(accessToken: string): Promise<AdultConsentStatus> {
  return request('/adult-consent/accept', { method: 'POST', accessToken });
}

export function fetchFeed(): Promise<{ items: FeedItem[] }> {
  return request('/feed');
}

export function fetchWallet(accessToken: string): Promise<WalletBalance> {
  return request('/wallet/me', { accessToken });
}

export const fetchWalletBalance = fetchWallet;

export function fetchCreditPackages(): Promise<{ items: CreditPackage[] }> {
  return request('/billing/packages');
}

export function createPaymentOrder(accessToken: string, packageCode: string): Promise<PaymentOrder> {
  return request('/billing/orders', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ package_code: packageCode, provider: 'crocopay' }),
  });
}

export function initiateCrocoPayCheckout(
  accessToken: string,
  orderId: string,
): Promise<{ order: PaymentOrder; redirect_url: string }> {
  return request(`/billing/orders/${orderId}/crocopay`, { method: 'POST', accessToken });
}

export function fetchMyGenerations(accessToken: string): Promise<GenerationListResponse> {
  return request('/generations', { accessToken });
}

export function fetchGenerationTask(accessToken: string, taskId: string): Promise<GenerationTask> {
  return request(`/generations/${taskId}`, { accessToken });
}

export function createGeneration(
  accessToken: string,
  payload: {
    model_code: string;
    operation: string;
    request_payload: Record<string, unknown>;
  },
): Promise<GenerationTask> {
  return request('/generations', {
    method: 'POST',
    accessToken,
    body: JSON.stringify(payload),
  });
}

export function importExternalMedia(accessToken: string, assetId: string): Promise<unknown> {
  return request(`/media/assets/${assetId}/import-external`, { method: 'POST', accessToken });
}

export function publishResultAsset(accessToken: string, assetId: string): Promise<unknown> {
  return request('/publications', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({
      asset_id: assetId,
      visibility: 'profile',
      is_explicit: true,
      blur_required: true,
      allow_remix: true,
      prompt_public: false,
    }),
  });
}

export function createProject(
  accessToken: string,
  payload: { title: string; description?: string; output_format: string },
): Promise<{ id: string }> {
  return request('/workspace/projects', { method: 'POST', accessToken, body: JSON.stringify(payload) });
}

export function createAvatar(accessToken: string, name: string): Promise<{ id: string }> {
  return request('/workspace/avatars', {
    method: 'POST',
    accessToken,
    body: JSON.stringify({ name }),
  });
}

export function fetchProfile(accessToken: string): Promise<UserProfile> {
  return request('/profiles/me', { accessToken });
}

export function updateProfile(
  accessToken: string,
  payload: Partial<Pick<UserProfile, 'display_name' | 'bio' | 'visibility'>>,
): Promise<UserProfile> {
  return request('/profiles/me', { method: 'PATCH', accessToken, body: JSON.stringify(payload) });
}

async function request<T>(
  path: string,
  options: RequestInit & { accessToken?: string } = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (options.accessToken) headers.set('Authorization', `Bearer ${options.accessToken}`);
  const response = await fetch(`${CORE_API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep status fallback when the upstream does not return JSON.
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
