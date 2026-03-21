export default function StatusChip({ label, tone = 'neutral' }) {
  return <span className={`status-chip status-chip--${tone}`}>{label}</span>;
}
