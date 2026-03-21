function toneFromGrade(grade) {
  const normalized = String(grade || '').toUpperCase();
  if (normalized === 'A') return 'a';
  if (normalized === 'B') return 'b';
  if (normalized === 'C') return 'c';
  return 'excluded';
}

export default function ScorePill({ score, grade }) {
  const tone = toneFromGrade(grade);
  return <span className={`score-pill score-pill--${tone}`}>SCORE {score}</span>;
}
