"use client";

import SurfaceCard from '../ui/SurfaceCard';

function initialsFromEmail(email) {
  const fallback = 'ME';
  if (!email) return fallback;
  const base = String(email).split('@')[0].trim();
  if (!base) return fallback;
  const letters = base.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
  if (letters.length >= 2) return letters.slice(0, 2);
  if (letters.length === 1) return `${letters}·`;
  return fallback;
}

export default function ProfileIdentityCard({ email }) {
  return (
    <SurfaceCard className="profile-mini-card" tone="glass">
      <p className="kicker">PROFILE</p>
      <h4>내 프로필</h4>
      <div className="profile-identity-block">
        <div className="profile-avatar" aria-hidden="true">{initialsFromEmail(email)}</div>
        <div>
          <p className="profile-email-label">이메일</p>
          <p className="profile-email">{email || '-'}</p>
        </div>
      </div>
    </SurfaceCard>
  );
}
