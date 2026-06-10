import { useGameStore } from '../../store/useGameStore';
import type { FlightResult } from '../../types';

function formatDeparture(iso: string): string {
  return iso.slice(11, 16); // "HH:mm"
}

function formatPrice(krw: number): string {
  return krw.toLocaleString('ko-KR') + '원';
}

function flightLabel(f: FlightResult): string {
  return `${f.airline} ${f.flight_number} ${formatPrice(f.price_krw)} (${formatDeparture(f.departure)} 출발) 선택`;
}

export default function SelectionMenu() {
  const selections    = useGameStore((s) => s.selections);
  const flightResults = useGameStore((s) => s.flightResults);
  const inputLocked   = useGameStore((s) => s.inputLocked);
  const isLoading     = useGameStore((s) => s.isLoading);
  const sendMessage   = useGameStore((s) => s.sendMessage);

  if (!inputLocked || isLoading) return null;

  if (flightResults.length > 0) {
    return (
      <div className="flex flex-col gap-2 animate-fade-in">
        {flightResults.map((flight) => (
          <button
            key={flight.flight_number}
            onClick={() => void sendMessage(flightLabel(flight))}
            className="rounded-2xl bg-game-navy/90 px-5 py-3 text-left text-white
                       transition-colors hover:bg-game-pink/80 shadow-md"
          >
            <span className="font-semibold">{flight.airline}</span>
            <span className="mx-2 text-white/40">|</span>
            <span className="text-game-pink font-bold">{formatPrice(flight.price_krw)}</span>
            <span className="mx-2 text-white/40">|</span>
            <span>{formatDeparture(flight.departure)} 출발</span>
          </button>
        ))}
      </div>
    );
  }

  if (selections.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 animate-fade-in">
      {selections.map((option) => (
        <button
          key={option}
          onClick={() => void sendMessage(option)}
          className="rounded-2xl bg-game-navy/90 px-5 py-3 text-left text-white
                     transition-colors hover:bg-game-pink/80 shadow-md"
        >
          {option}
        </button>
      ))}
    </div>
  );
}
