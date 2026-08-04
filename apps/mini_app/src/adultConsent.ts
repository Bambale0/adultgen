import { getCoreApiBaseUrl } from './env';

export type AdultConsentStatus = {
  accepted: boolean;
  policy_version: string;
  accepted_at: string | null;
};

export async function fetchAdultConsentStatus(accessToken: string): Promise<AdultConsentStatus> {
  const response = await fetch(`${getCoreApiBaseUrl()}/adult-consent`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Adult consent status request failed.');
  }

  return (await response.json()) as AdultConsentStatus;
}

export async function acceptAdultConsent(accessToken: string): Promise<AdultConsentStatus> {
  const response = await fetch(`${getCoreApiBaseUrl()}/adult-consent/accept`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Adult consent accept request failed.');
  }

  return (await response.json()) as AdultConsentStatus;
}
