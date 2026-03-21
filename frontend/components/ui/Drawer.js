"use client";

import { useEffect } from 'react';

export default function Drawer({ open, onClose, title, children, side = 'right', width = '520px' }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="ui-drawer-overlay" onClick={onClose} role="presentation">
      <aside
        className={`ui-drawer ui-drawer--${side}`}
        style={side === 'right' ? { width } : undefined}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label={title}
      >
        <header className="ui-drawer-header">
          <h3>{title}</h3>
          <button type="button" className="btn btn-ghost" onClick={onClose} aria-label="드로어 닫기">
            닫기
          </button>
        </header>
        <div className="ui-drawer-body">{children}</div>
      </aside>
    </div>
  );
}
