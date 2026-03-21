"use client";

import { useEffect, useRef, useState } from 'react';

export default function usePresence(open, { enterDelay = 16, exitDuration = 200 } = {}) {
  const [mounted, setMounted] = useState(open);
  const [visible, setVisible] = useState(open);
  const timerRef = useRef(null);
  const frameRef = useRef(null);

  useEffect(() => {
    if (frameRef.current) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    if (open) {
      setMounted(true);
      frameRef.current = requestAnimationFrame(() => {
        timerRef.current = setTimeout(() => {
          setVisible(true);
        }, enterDelay);
      });
      return undefined;
    }

    if (!mounted) return undefined;

    setVisible(false);
    timerRef.current = setTimeout(() => {
      setMounted(false);
    }, exitDuration);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [open, enterDelay, exitDuration]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return { mounted, visible };
}
