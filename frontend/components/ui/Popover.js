"use client";

import { useEffect, useRef, useState } from 'react';

import { MOTION } from '../../lib/motion';
import usePresence from './usePresence';

export default function Popover({
  triggerLabel,
  triggerClassName = '',
  panelClassName = '',
  children,
  ariaLabel,
  align = 'left',
  trigger,
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const { mounted, visible } = usePresence(open, { exitDuration: MOTION.durationFast });

  useEffect(() => {
    if (!mounted) return undefined;

    const onMouseDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [mounted]);

  const triggerProps = {
    onClick: () => setOpen((prev) => !prev),
    'aria-label': ariaLabel || triggerLabel || '팝오버 열기',
    'aria-expanded': open,
  };

  return (
    <span className="ui-popover" ref={rootRef}>
      {trigger ? (
        typeof trigger === 'function' ? (
          trigger({ ...triggerProps, open })
        ) : (
          trigger
        )
      ) : (
        <button type="button" className={`btn btn-ghost ${triggerClassName}`.trim()} {...triggerProps}>
          {triggerLabel}
        </button>
      )}
      {mounted && (
        <div
          className={`ui-popover-panel ui-popover-panel--${align} ${panelClassName}`.trim()}
          data-state={visible ? 'open' : 'closing'}
          role="dialog"
        >
          {children}
        </div>
      )}
    </span>
  );
}
