export type EmotionCode = 'idle' | 'smile' | 'sad' | 'surprise';

export interface FlightResult {
  airline: string;
  flight_number: string;
  departure: string;
  arrival: string;
  price_krw: number;
  duration: string;
  stops: number;
}

export interface ChatRequest {
  session_id: string;
  user_message: string;
  current_chapter: number;
  current_affinity: number;
}

export interface TurnResult {
  next_chapter: number | null; // null/현재값이면 전환 없음
  affinity_delta: number;
  agent_dialogue_list: string[];
  emotion_code: EmotionCode;
  metadata: Record<string, unknown>;
}
