import os
import json
from datetime import date
from openai import OpenAI


def _build_system_prompt() -> str:
    """현재 날짜를 주입한 의도 분류 시스템 프롬프트 생성.

    연도 미지정 날짜는 '내년(올해+1)'으로 보정하도록 지시한다.
    예시 날짜도 내년 기준으로 생성하여 모델이 과거 연도로 편향되지 않게 한다.
    """
    today = date.today()
    this_year = today.year
    next_year = today.year + 1
    return f"""당신은 여행 메이트 게임의 의도 분류기입니다.
사용자의 발화를 분석하여 아래 세 가지 의도 중 하나로 분류하고, JSON 형식으로만 응답하세요.

오늘 날짜는 {today.isoformat()}입니다.

의도 유형:
- "dialogue": 일반 대화 (인사, 감정 표현, 잡담 등)
- "tool": 항공편 검색이 필요한 발화 (출발지/목적지/날짜 언급 또는 항공편 문의)
- "selection": 제시된 선택지에 대한 응답 (번호 선택, "첫 번째", "그걸로" 등)

tool 의도 시 params에서 IATA 코드로 공항을 추출하세요.
주요 공항 IATA: 인천=ICN, 김포=GMP, 부산=PUS, 도쿄(나리타)=NRT, 도쿄(하네다)=HND, 오사카=KIX, 파리=CDG, 런던=LHR, 방콕=BKK, 뉴욕=JFK, 싱가포르=SIN

날짜 규칙 (매우 중요):
- 날짜를 전혀 언급하지 않으면 date를 null로 두세요.
- 월/일만 말하고 연도를 말하지 않으면, **무조건 내년({next_year})으로 설정하세요.**
  해당 날짜가 올해({this_year}) 안에 아직 오지 않았더라도, 올해({this_year}) 연도는 절대 쓰지 말고 반드시 {next_year}을 사용하세요.
- 연도를 명시한 경우에만 그 연도를 그대로 사용하세요.

응답 형식 (JSON only):
{{
  "intent": "dialogue" | "tool" | "selection",
  "params": {{
    // tool인 경우: {{"origin": "ICN", "destination": "NRT", "date": "{next_year}-08-01" or null, "adults": 1}}
    // selection인 경우: {{"selected_option": "선택한 내용"}}
    // dialogue인 경우: {{}}
  }},
  "reason": "분류 이유 한 줄"
}}

예시:
사용자: "안녕! 오늘 날씨 어때?"
→ {{"intent": "dialogue", "params": {{}}, "reason": "일반 인사말"}}

사용자: "서울에서 도쿄 가는 비행기 찾아줘"
→ {{"intent": "tool", "params": {{"origin": "ICN", "destination": "NRT", "date": null, "adults": 1}}, "reason": "항공편 검색 요청(날짜 미언급)"}}

사용자: "8월 15일에 인천에서 파리 가고 싶어"  (오늘이 {today.isoformat()}이라 8월 15일이 올해 안에 아직 안 왔어도 내년으로)
→ {{"intent": "tool", "params": {{"origin": "ICN", "destination": "CDG", "date": "{next_year}-08-15", "adults": 1}}, "reason": "연도 미지정 → 무조건 내년({next_year})으로 보정"}}

사용자: "2번으로 할게"
→ {{"intent": "selection", "params": {{"selected_option": "2번"}}, "reason": "선택지 응답"}}"""


class IntentClassifier:
    def __init__(self):
        self._client = OpenAI(
            api_key=os.getenv("UPSTAGE_API_KEY"),
            base_url="https://api.upstage.ai/v1",
        )

    def classify(self, user_message: str, current_chapter: int, current_affinity: int) -> dict:
        """
        Returns:
            {
                "intent": "dialogue" | "tool" | "selection",
                "params": dict,
                "reason": str
            }
        """
        user_context = (
            f"현재 챕터: {current_chapter}, 현재 호감도: {current_affinity}\n"
            f"사용자 발화: {user_message}"
        )

        try:
            response = self._client.chat.completions.create(
                model="solar-pro",
                messages=[
                    {"role": "system", "content": _build_system_prompt()},
                    {"role": "user", "content": user_context},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=256,
            )
            result = json.loads(response.choices[0].message.content)
            return self._validate(result)
        except Exception:
            return {"intent": "dialogue", "params": {}, "reason": "분류 실패 - 기본값 반환"}

    def _validate(self, result: dict) -> dict:
        intent = result.get("intent", "dialogue")
        if intent not in ("dialogue", "tool", "selection"):
            intent = "dialogue"

        params = result.get("params", {})
        if intent == "tool":
            params.setdefault("origin", "ICN")
            params.setdefault("destination", None)
            params.setdefault("date", None)
            params.setdefault("adults", 1)

        return {
            "intent": intent,
            "params": params,
            "reason": result.get("reason", ""),
        }
