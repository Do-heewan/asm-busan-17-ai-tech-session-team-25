import { useGameStore } from '../store/useGameStore';

export default function TitleScreen() {
  const startGame = useGameStore((s) => s.startGame);
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-8 bg-gradient-to-b from-game-pink-light to-game-pink/40">
      <h1 className="text-4xl font-bold text-game-pink-dark drop-shadow">✈️ 나만의 여행 메이트</h1>
      <p className="text-game-navy">메이트와 대화하며 함께 여행을 떠나보세요</p>
      <button
        onClick={startGame}
        className="rounded-full bg-game-pink px-8 py-3 text-lg font-semibold text-white shadow-lg transition-colors hover:bg-game-pink-dark"
      >
        시작하기
      </button>
    </div>
  );
}
