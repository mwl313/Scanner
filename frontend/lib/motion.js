export const MOTION = {
  durationFast: 160,
  durationBase: 240,
  durationSlow: 320,
  easingStandard: 'cubic-bezier(0.22, 1, 0.36, 1)',
  easingExit: 'cubic-bezier(0.4, 0, 1, 1)',
  distanceSm: 6,
  distanceMd: 10,
  distanceLg: 18,
};

export function ms(value) {
  return `${value}ms`;
}
