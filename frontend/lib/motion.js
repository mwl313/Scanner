export const MOTION = {
  durationFast: 180,
  durationBase: 260,
  durationSlow: 320,
  easingSmooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingSmoothInOut: 'cubic-bezier(0.42, 0, 0.18, 1)',
  easingStandard: 'cubic-bezier(0.4, 0, 0.2, 1)',
  easingExit: 'cubic-bezier(0.42, 0, 0.18, 1)',
  distanceSm: 6,
  distanceMd: 10,
  distanceLg: 18,
};

export function ms(value) {
  return `${value}ms`;
}
