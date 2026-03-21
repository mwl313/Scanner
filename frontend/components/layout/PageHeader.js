import FadeIn from '../ui/FadeIn';

export default function PageHeader({ title, subtitle, actions }) {
  return (
    <FadeIn className="page-header">
      <div>
        <h1>{title}</h1>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </FadeIn>
  );
}
