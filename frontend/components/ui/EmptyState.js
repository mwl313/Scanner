export default function EmptyState({ title, description }) {
  return (
    <div className="state-block state-empty">
      <p className="state-title">{title}</p>
      {description && <p className="state-desc">{description}</p>}
    </div>
  );
}
