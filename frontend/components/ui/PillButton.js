export default function PillButton({ className = '', type = 'button', ...props }) {
  return <button type={type} className={`btn btn-primary ${className}`.trim()} {...props} />;
}
