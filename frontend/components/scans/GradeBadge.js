import { GRADE_META } from '../../lib/theme';

export default function GradeBadge({ grade }) {
  const meta = GRADE_META[grade] || GRADE_META.EXCLUDED;
  return <span className={`grade-badge grade-badge--${meta.tone}`}>{meta.label}</span>;
}
