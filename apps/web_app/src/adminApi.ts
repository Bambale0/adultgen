const CORE_API_URL = import.meta.env.VITE_CORE_API_URL || '/api';

export type AdminUser = {
  id: string; telegram_user_id: number; username: string | null; is_blocked: boolean;
  can_generate: boolean; can_publish_profile: boolean; can_publish_feed: boolean;
  can_use_payments: boolean; cached_available_balance: number | null;
};
export type AdminGeneration = { id: string; user_id: string; status: string; model_code: string; operation: string; charged_credits: number };
export type AdminPublication = { id: string; user_id: string; title: string | null; status: string; visibility: string; media_url: string };
export type AdminPaymentOrder = { id: string; user_id: string; provider: string; package_code: string; amount_minor: number; currency: string; status: string };
export type AdminAuditEvent = { id: string; target_type: string; target_id: string | null; action: string; reason: string | null; created_at: string };

export const fetchAdminUsers = (token: string) => adminRequest<{ items: AdminUser[] }>('/admin/users', token);
export const fetchAdminGenerations = (token: string) => adminRequest<{ items: AdminGeneration[] }>('/admin/generations', token);
export const fetchAdminPublications = (token: string) => adminRequest<{ items: AdminPublication[] }>('/admin/publications', token);
export const fetchAdminPaymentOrders = (token: string) => adminRequest<{ items: AdminPaymentOrder[] }>('/admin/payments/orders', token);
export const fetchAdminAuditEvents = (token: string) => adminRequest<{ items: AdminAuditEvent[] }>('/admin/audit/events', token);

export function updateAdminUserCapabilities(token: string, userId: string, patch: Record<string, boolean>, reason: string) {
  return adminRequest<AdminUser>(`/admin/users/${userId}/capabilities`, token, {
    method: 'PATCH', body: JSON.stringify({ ...patch, reason }),
  });
}

export function applyAdminPublicationAction(token: string, publicationId: string, action: 'hide' | 'restore' | 'delete', reason: string) {
  return adminRequest<AdminPublication>(`/admin/publications/${publicationId}/actions`, token, {
    method: 'POST', body: JSON.stringify({ action, reason }),
  });
}

export function createAdminWalletAdjustment(token: string, userId: string, amount: number, reason: string) {
  return adminRequest('/admin/wallet/adjustments', token, {
    method: 'POST', body: JSON.stringify({ user_id: userId, amount, bucket: 'bonus', reason }),
  });
}

async function adminRequest<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${CORE_API_URL}${path}`, { ...options, headers });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}
