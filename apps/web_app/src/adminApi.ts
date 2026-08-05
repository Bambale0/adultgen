export type AdminUser = {
  id: string;
  telegram_user_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  is_blocked: boolean;
  can_generate: boolean;
  can_publish_profile: boolean;
  can_publish_feed: boolean;
  can_use_payments: boolean;
  cached_available_balance: number | null;
  cached_reserved_balance: number | null;
  created_at: string;
  updated_at: string;
};

export type AdminGeneration = {
  id: string;
  user_id: string;
  status: string;
  provider: string;
  model_code: string;
  operation: string;
  reserved_credits: number;
  charged_credits: number;
  provider_task_id: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminPublication = {
  id: string;
  user_id: string;
  asset_id: string;
  visibility: string;
  status: string;
  title: string | null;
  description: string | null;
  is_explicit: boolean;
  blur_required: boolean;
  published_at: string | null;
  deleted_at: string | null;
  media_url: string;
};

export type AdminPaymentOrder = {
  id: string;
  user_id: string;
  provider: string;
  external_payment_id: string | null;
  package_code: string;
  amount_minor: number;
  currency: string;
  credits_amount: number;
  status: string;
  expires_at: string;
  paid_at: string | null;
  provider_checkout_url: string | null;
  created_at: string;
  updated_at: string;
};

export type AdminWalletAdjustment = {
  user_id: string;
  operation_id: string;
  amount: number;
  bucket: string;
  total_available: number;
  total_reserved: number;
};

export type AdminAuditEvent = {
  id: string;
  admin_user_id: string | null;
  target_type: string;
  target_id: string | null;
  action: string;
  reason: string | null;
  before_state: Record<string, unknown>;
  after_state: Record<string, unknown>;
  created_at: string;
};

const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export async function fetchAdminUsers(adminToken: string, limit = 50): Promise<{ items: AdminUser[] }> {
  return adminRequest(`/admin/users?limit=${limit}`, adminToken);
}

export async function updateAdminUserCapabilities(
  adminToken: string,
  userId: string,
  payload: {
    is_blocked?: boolean;
    can_generate?: boolean;
    can_publish_profile?: boolean;
    can_publish_feed?: boolean;
    can_use_payments?: boolean;
    reason: string;
  },
): Promise<AdminUser> {
  return adminRequest(`/admin/users/${userId}/capabilities`, adminToken, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function fetchAdminGenerations(
  adminToken: string,
  limit = 50,
  status?: string,
): Promise<{ items: AdminGeneration[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set('status', status);
  return adminRequest(`/admin/generations?${params.toString()}`, adminToken);
}

export async function fetchAdminPublications(
  adminToken: string,
  limit = 50,
  status?: string,
): Promise<{ items: AdminPublication[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set('status', status);
  return adminRequest(`/admin/publications?${params.toString()}`, adminToken);
}

export async function applyAdminPublicationAction(
  adminToken: string,
  publicationId: string,
  action: 'hide' | 'restore' | 'delete',
  reason: string,
): Promise<AdminPublication> {
  return adminRequest(`/admin/publications/${publicationId}/actions`, adminToken, {
    method: 'POST',
    body: JSON.stringify({ action, reason }),
  });
}

export async function fetchAdminPaymentOrders(
  adminToken: string,
  limit = 50,
  status?: string,
): Promise<{ items: AdminPaymentOrder[] }> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (status) params.set('status', status);
  return adminRequest(`/admin/payments/orders?${params.toString()}`, adminToken);
}

export async function createAdminWalletAdjustment(
  adminToken: string,
  payload: {
    user_id: string;
    amount: number;
    bucket: 'purchased' | 'subscription' | 'bonus';
    reason: string;
    admin_user_id?: string | null;
  },
): Promise<AdminWalletAdjustment> {
  return adminRequest('/admin/wallet/adjustments', adminToken, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchAdminAuditEvents(adminToken: string, limit = 50): Promise<{ items: AdminAuditEvent[] }> {
  return adminRequest(`/admin/audit/events?limit=${limit}`, adminToken);
}

async function adminRequest<T = unknown>(
  path: string,
  adminToken: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('Authorization', `Bearer ${adminToken}`);

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
  return response.json() as Promise<T>;
}
