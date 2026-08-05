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
  created_at: string;
  updated_at: string;
};

export type AdminGeneration = {
  id: string;
  user_id: string;
  provider: string;
  model_code: string;
  operation: string;
  status: string;
  provider_task_id: string | null;
  reserved_credits: number;
  charged_credits: number;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  submitted_at: string | null;
  completed_at: string | null;
};

export type AdminPublication = {
  id: string;
  user_id: string;
  asset_id: string;
  title: string | null;
  visibility: string;
  is_explicit: boolean;
  blur_required: boolean;
  status: string;
  published_at: string;
  deleted_at: string | null;
};

export type AdminPaymentOrder = {
  id: string;
  user_id: string;
  provider: string;
  package_code: string;
  amount_minor: number;
  currency: string;
  credits_amount: number;
  status: string;
  external_payment_id: string | null;
  provider_checkout_url: string | null;
  expires_at: string;
  paid_at: string | null;
  created_at: string;
  updated_at: string;
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

export type AdminWalletAdjustment = {
  user_id: string;
  amount: number;
  bucket: string;
  total_available: number;
  total_reserved: number;
};

const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export async function fetchAdminUsers(adminToken: string): Promise<{ items: AdminUser[] }> {
  return adminRequest<{ items: AdminUser[] }>('/admin/users', adminToken);
}

export async function patchAdminUserFlags(
  adminToken: string,
  userId: string,
  payload: Partial<Pick<AdminUser, 'is_blocked' | 'can_generate' | 'can_publish_profile' | 'can_publish_feed' | 'can_use_payments'>> & {
    reason: string;
    admin_user_id?: string | null;
  },
): Promise<AdminUser> {
  return adminRequest<AdminUser>(`/admin/users/${userId}/flags`, adminToken, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function fetchAdminGenerations(adminToken: string): Promise<{ items: AdminGeneration[] }> {
  return adminRequest<{ items: AdminGeneration[] }>('/admin/generations', adminToken);
}

export async function fetchAdminPublications(adminToken: string): Promise<{ items: AdminPublication[] }> {
  return adminRequest<{ items: AdminPublication[] }>('/admin/publications', adminToken);
}

export async function patchAdminPublicationStatus(
  adminToken: string,
  publicationId: string,
  payload: { status: string; reason: string; admin_user_id?: string | null },
): Promise<AdminPublication> {
  return adminRequest<AdminPublication>(`/admin/publications/${publicationId}/status`, adminToken, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function fetchAdminPaymentOrders(adminToken: string): Promise<{ items: AdminPaymentOrder[] }> {
  return adminRequest<{ items: AdminPaymentOrder[] }>('/admin/payments/orders', adminToken);
}

export async function createAdminWalletAdjustment(
  adminToken: string,
  payload: { user_id: string; amount: number; bucket: string; reason: string; admin_user_id?: string | null },
): Promise<AdminWalletAdjustment> {
  return adminRequest<AdminWalletAdjustment>('/admin/wallet-adjustments', adminToken, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchAdminAuditEvents(adminToken: string): Promise<{ items: AdminAuditEvent[] }> {
  return adminRequest<{ items: AdminAuditEvent[] }>('/admin/audit-events', adminToken);
}

async function adminRequest<T>(path: string, adminToken: string, options: RequestInit = {}): Promise<T> {
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
