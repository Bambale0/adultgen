import { useEffect, useState } from 'react';

import { fetchMyProfile, updateMyProfile, type UserProfile } from './profile';

export function ProfileVisibilityPage({ accessToken }: { accessToken: string }) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'saving' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadProfile() {
      try {
        const loadedProfile = await fetchMyProfile(accessToken);
        if (!cancelled) {
          setProfile(loadedProfile);
          setStatus('ready');
        }
      } catch (caughtError) {
        if (!cancelled) {
          setStatus('error');
          setError(caughtError instanceof Error ? caughtError.message : 'Profile request failed.');
        }
      }
    }

    void loadProfile();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function setVisibility(visibility: 'public' | 'private') {
    setStatus('saving');
    setError(null);
    try {
      const updatedProfile = await updateMyProfile(accessToken, { visibility });
      setProfile(updatedProfile);
      setStatus('ready');
    } catch (caughtError) {
      setStatus('error');
      setError(caughtError instanceof Error ? caughtError.message : 'Profile update failed.');
    }
  }

  return (
    <section className="page-card profile-card">
      <p className="eyebrow">Public/private</p>
      <h1>Профиль</h1>
      <p>
        Управляйте видимостью профиля. Публичная ссылка использует безопасный public_id,
        а не Telegram ID или внутренний UUID.
      </p>

      {profile && (
        <div className="profile-panel">
          <span>public_id: {profile.public_id}</span>
          <strong>{profile.visibility === 'public' ? 'Публичный' : 'Приватный'}</strong>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}

      <div className="button-row">
        <button
          className="primary-button"
          type="button"
          disabled={status === 'saving'}
          onClick={() => void setVisibility('public')}
        >
          Сделать публичным
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={status === 'saving'}
          onClick={() => void setVisibility('private')}
        >
          Сделать приватным
        </button>
      </div>
    </section>
  );
}
