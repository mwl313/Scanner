export default function FadeIn({ children, delay = 0, className = '' }) {
  return (
    <div className={`fade-in ${className}`.trim()} style={{ animationDelay: `${delay}ms` }}>
      {children}
    </div>
  );
}
