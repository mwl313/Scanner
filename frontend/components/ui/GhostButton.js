export default function GhostButton({ className = '', type = 'button', ...props }) {
  return <button type={type} className={`btn btn-ghost ${className}`.trim()} {...props} />;
}
