import { getCoreApiBaseUrl } from './env';

export type AvatarProfile = {
  id: string;
  name: string;
  status: string;
};

export type Project = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  output_format: string;
};

export type Scene = {
  id: string;
  project_id: string;
  order_index: number;
  title: string | null;
  prompt: string;
  duration_seconds: number;
  aspect_ratio: string;
  status: string;
};

export async function createAvatarProfile(
  accessToken: string,
  name: string,
): Promise<AvatarProfile> {
  return postJson<AvatarProfile>(accessToken, '/workspace/avatars', { name });
}

export async function createProject(
  accessToken: string,
  payload: {
    title: string;
    description?: string | null;
    output_format?: string;
  },
): Promise<Project> {
  return postJson<Project>(accessToken, '/workspace/projects', {
    title: payload.title,
    description: payload.description ?? null,
    output_format: payload.output_format ?? '9:16',
  });
}

export async function createScene(
  accessToken: string,
  projectId: string,
  payload: {
    prompt: string;
    title?: string | null;
    duration_seconds?: number;
    aspect_ratio?: string;
    camera_notes?: string | null;
    action_notes?: string | null;
    audio_notes?: string | null;
  },
): Promise<Scene> {
  return postJson<Scene>(accessToken, `/workspace/projects/${projectId}/scenes`, {
    prompt: payload.prompt,
    title: payload.title ?? null,
    duration_seconds: payload.duration_seconds ?? 5,
    aspect_ratio: payload.aspect_ratio ?? '9:16',
    camera_notes: payload.camera_notes ?? null,
    action_notes: payload.action_notes ?? null,
    audio_notes: payload.audio_notes ?? null,
  });
}

async function postJson<T>(accessToken: string, path: string, body: object): Promise<T> {
  const response = await fetch(`${getCoreApiBaseUrl()}${path}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = typeof payload?.detail === 'string' ? payload.detail : 'Workspace request failed.';
    throw new Error(detail);
  }

  return (await response.json()) as T;
}
