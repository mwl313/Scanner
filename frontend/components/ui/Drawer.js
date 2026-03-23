"use client";

import { useEffect, useRef } from 'react';

import { MOTION } from '../../lib/motion';
import usePresence from './usePresence';

export default function Drawer({ open, onClose, title, children, side = 'right', width = '520px' }) {
  const closeButtonRef = useRef(null);
  const lastFocusedElementRef = useRef(null);
  const { mounted, visible } = usePresence(open, { exitDuration: MOTION.durationSlow });

  useEffect(() => {
    if (!mounted) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [mounted, onClose]);

  useEffect(() => {
    if (!mounted) return undefined;
    const root = document.documentElement;
    const previousRootOverflow = root.style.overflow;
    const previousRootOverscroll = root.style.overscrollBehavior;
    const previousOverflow = document.body.style.overflow;
    const previousOverscroll = document.body.style.overscrollBehavior;
    document.body.style.overflow = 'hidden';
    document.body.style.overscrollBehavior = 'none';
    root.style.overflow = 'hidden';
    root.style.overscrollBehavior = 'none';
    return () => {
      document.body.style.overflow = previousOverflow;
      document.body.style.overscrollBehavior = previousOverscroll;
      root.style.overflow = previousRootOverflow;
      root.style.overscrollBehavior = previousRootOverscroll;
    };
  }, [mounted]);

  useEffect(() => {
    if (!open) return;
    lastFocusedElementRef.current = document.activeElement;
    const id = setTimeout(() => {
      closeButtonRef.current?.focus();
    }, 20);
    return () => clearTimeout(id);
  }, [open]);

  useEffect(() => {
    if (mounted) return;
    if (lastFocusedElementRef.current && typeof lastFocusedElementRef.current.focus === 'function') {
      lastFocusedElementRef.current.focus();
    }
  }, [mounted]);

  if (!mounted) return null;

  return (
    <div
      className="ui-drawer-overlay"
      data-state={visible ? 'open' : 'closing'}
      onClick={onClose}
      role="presentation"
      aria-hidden={!visible}
    >
      <aside
        className={`ui-drawer ui-drawer--${side}`}
        style={side === 'right' ? { width } : undefined}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header className="ui-drawer-header">
          <h3>{title}</h3>
          <button ref={closeButtonRef} type="button" className="btn btn-ghost" onClick={onClose} aria-label="드로어 닫기">
            닫기
          </button>
        </header>
        <div className="ui-drawer-body">{children}</div>
      </aside>
    </div>
  );
}
