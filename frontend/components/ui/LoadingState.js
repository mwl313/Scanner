export default function LoadingState({ message = '데이터를 불러오는 중...' }) {
  return (
    <div className="state-block state-loading">
      <div className="state-shimmer" />
      <p>{message}</p>
    </div>
  );
}
