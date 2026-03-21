export default function SurfaceCard({ as = 'section', tone = 'default', className = '', children }) {
  const Component = as;
  const toneClass = tone === 'soft' ? 'surface-card--soft' : tone === 'glass' ? 'surface-card--glass' : 'surface-card--default';
  return <Component className={`surface-card ${toneClass} ${className}`.trim()}>{children}</Component>;
}
