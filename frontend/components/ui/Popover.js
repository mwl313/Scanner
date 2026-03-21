"use client";

import { useEffect, useRef, useState } from 'react';

export default function Popover({ triggerLabel, triggerClassName = '', panelClassName = '', children, ariaLabel }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onMouseDown = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onMouseDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, [open]);

  return (
    <span className="ui-popover" ref={rootRef}>
      <button
        type="button"
        className={`btn btn-ghost ${triggerClassName}`.trim()}
        onClick={() => setOpen((prev) => !prev)}
        aria-label={ariaLabel || triggerLabel}
      >
        {triggerLabel}
      </button>
      {open && <div className={`ui-popover-panel ${panelClassName}`.trim()}>{children}</div>}
    </span>
  );
}
