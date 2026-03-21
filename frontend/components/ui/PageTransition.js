"use client";

import { useEffect, useMemo, useRef, useState } from 'react';

import { MOTION } from '../../lib/motion';
import { resolveRouteTransitionIndex } from '../../lib/theme';

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return undefined;
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = () => setReduced(media.matches);
    handleChange();
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, []);

  return reduced;
}

export default function PageTransition({ children, pathname }) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const animationTimeoutRef = useRef(null);
  const animationFrameRef = useRef(null);
  const currentPathRef = useRef(pathname || '');
  const currentNodeRef = useRef(children);

  const [state, setState] = useState({
    currentPath: pathname || '',
    currentNode: children,
    previousNode: null,
    direction: 0,
    running: false,
  });

  const direction = useMemo(() => {
    const prevIndex = resolveRouteTransitionIndex(currentPathRef.current);
    const nextIndex = resolveRouteTransitionIndex(pathname || '');
    if (nextIndex === prevIndex) return 0;
    return nextIndex > prevIndex ? 1 : -1;
  }, [pathname]);

  useEffect(() => {
    if (animationTimeoutRef.current) {
      clearTimeout(animationTimeoutRef.current);
      animationTimeoutRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if ((pathname || '') === currentPathRef.current) {
      currentNodeRef.current = children;
      return undefined;
    }

    if (prefersReducedMotion) {
      currentPathRef.current = pathname || '';
      currentNodeRef.current = children;
      setState({
        currentPath: pathname || '',
        currentNode: children,
        previousNode: null,
        direction: 0,
        running: false,
      });
      return undefined;
    }

    const previousNode = currentNodeRef.current;
    currentPathRef.current = pathname || '';
    currentNodeRef.current = children;

    setState({
      currentPath: pathname || '',
      currentNode: children,
      previousNode,
      direction,
      running: false,
    });

    animationFrameRef.current = requestAnimationFrame(() => {
      setState((prev) => ({ ...prev, running: true }));
    });

    animationTimeoutRef.current = setTimeout(() => {
      setState((prev) => ({ ...prev, previousNode: null, running: false }));
      animationTimeoutRef.current = null;
    }, MOTION.durationSlow);

    return () => {
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
        animationTimeoutRef.current = null;
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [children, direction, pathname, prefersReducedMotion]);

  const directionLabel = state.direction > 0 ? 'forward' : state.direction < 0 ? 'backward' : 'neutral';
  const currentLayerNode = state.previousNode ? state.currentNode : children;

  return (
    <div
      className={`page-transition ${state.previousNode ? 'is-stacked' : ''} ${state.running ? 'is-running' : ''}`.trim()}
      data-direction={directionLabel}
      data-running={state.running ? 'true' : 'false'}
    >
      {state.previousNode && (
        <div className="page-transition-layer page-transition-layer--previous" aria-hidden="true">
          {state.previousNode}
        </div>
      )}
      <div className="page-transition-layer page-transition-layer--current">{currentLayerNode}</div>
    </div>
  );
}
