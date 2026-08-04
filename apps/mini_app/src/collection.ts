import { getCoreApiBaseUrl } from './env';

export type SavedPublication = {
  publication_id: string;
  saved_at: string;
};

export async function listSavedPublications(accessToken: string): Promise<SavedPublication[]> {
  const response = await fetch(`${getCoreApiBaseUrl()}/collections/saved`, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Saved collection request failed.');
  }

  const payload = (await response.json()) as { items: SavedPublication[] };
  return payload.items;
}

export async function savePublication(
  accessToken: string,
  publicationId: string,
): Promise<SavedPublication> {
  const response = await fetch(`${getCoreApiBaseUrl()}/collections/saved/${publicationId}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === 'string' ? body.detail : 'Save publication failed.';
    throw new Error(detail);
  }

  return (await response.json()) as SavedPublication;
}

export async function unsavePublication(accessToken: string, publicationId: string): Promise<void> {
  const response = await fetch(`${getCoreApiBaseUrl()}/collections/saved/${publicationId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!response.ok) {
    throw new Error('Unsave publication failed.');
  }
}
