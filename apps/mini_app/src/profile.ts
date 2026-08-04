import { getCoreApiBaseUrl } from './env';

export type UserProfile = {
  id: string;
  public_id: string;
  display_name: string | null;
  bio: string | null;
  visibility: 'public' | 'private';
};

export async function fetchMyProfile(accessToken: string): Promise<UserProfile> {
  const response = await fetch(`${getCoreApiBaseUrl()}/profiles/me`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Profile request failed.');
  }

  return (await response.json()) as UserProfile;
}

export async function updateMyProfile(
  accessToken: string,
  payload: {
    display_name?: string | null;
    bio?: string | null;
    visibility?: 'public' | 'private';
  },
): Promise<UserProfile> {
  const response = await fetch(`${getCoreApiBaseUrl()}/profiles/me`, {
    method: 'PATCH',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === 'string' ? body.detail : 'Profile update failed.';
    throw new Error(detail);
  }

  return (await response.json()) as UserProfile;
}
