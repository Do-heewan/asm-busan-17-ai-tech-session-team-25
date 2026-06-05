"""
대사 생성 에이전트.

단기 메모리(대화 맥락), 호감도, 챕터, 그리고 도구 호출 결과(있다면)를 종합해
Solar LLM으로 캐릭터의 최종 대사 리스트와 표정(emotion_code)을 생성한다.

LLM이 불가능하거나(키 없음) 응답 파싱에 실패해도 더미 대사로 폴백하여
게임 턴이 항상 완결되도록 보장한다.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.prompts.system_prompts import build_system_prompt, FEW_SHOT_EXAMPLES
from app.services import llm_client

# response.py의 TurnResult.emotion_code와 동일한 허용 집합
_VALID_EMOTIONS = {"idle", "smile", "sad", "surprise"}
_DEFAULT_EMOTION = "idle"


@dataclass
class DialogueResult:
    """대사 생성 결과."""

    dialogue_list: List[str] = field(default_factory=list)
    emotion_code: str = _DEFAULT_EMOTION


def _build_messages(
    user_message: str,
    affinity: int,
    chapter: int,
    history: List[Dict[str, str]],
    tool_result: Optional[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """LLM에 보낼 messages 배열을 조립한다."""
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": build_system_prompt(affinity, chapter)}
    ]
    # Few-shot 예시로 출력 포맷/말투를 고정
    messages.extend(FEW_SHOT_EXAMPLES)
    # 단기 메모리(이전 대화)
    messages.extend(history)

    # 도구 호출 결과(항공권 등)가 있으면 사실 근거로 주입
    if tool_result:
        messages.append(
            {
                "role": "system",
                "content": (
                    "[도구 조회 결과] 아래 데이터에 근거해서만 사실(가격/일정 등)을 말한다:\n"
                    + json.dumps(tool_result, ensure_ascii=False)
                ),
            }
        )

    messages.append({"role": "user", "content": user_message})
    return messages


def _parse_llm_json(raw: str) -> Optional[DialogueResult]:
    """LLM 응답 문자열에서 {dialogue, emotion} JSON을 견고하게 파싱한다.

    코드블록 표시(```)나 앞뒤 잡텍스트가 섞여 와도 첫 JSON 오브젝트를 추출한다.
    파싱 실패 시 None을 반환해 호출측이 폴백하게 한다.
    """
    text = raw.strip()
    # ```json ... ``` 같은 코드펜스 제거
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    # 가장 바깥 중괄호 블록만 추출
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    dialogue = data.get("dialogue")
    # 문자열 단일 응답도 허용
    if isinstance(dialogue, str):
        dialogue = [dialogue]
    if not isinstance(dialogue, list) or not dialogue:
        return None
    dialogue = [str(d) for d in dialogue if str(d).strip()]
    if not dialogue:
        return None

    emotion = data.get("emotion", _DEFAULT_EMOTION)
    if emotion not in _VALID_EMOTIONS:
        emotion = _DEFAULT_EMOTION

    return DialogueResult(dialogue_list=dialogue, emotion_code=emotion)


def _fallback(user_message: str, affinity: int) -> DialogueResult:
    """LLM 없이 동작하는 더미 대사. 호감도에 따라 톤만 약간 달리한다."""
    if affinity >= 60:
        line = f"'{user_message}'라니 너랑 있으면 뭘 해도 설렌다니까 ㅎㅎ"
        emotion = "smile"
    elif affinity >= 30:
        line = f"오 '{user_message}'? 좋은데! 우리 같이 더 얘기해보자!"
        emotion = "smile"
    else:
        line = f"응, '{user_message}' 말이지? 좀 더 들려줄래?"
        emotion = "idle"
    return DialogueResult(dialogue_list=[line], emotion_code=emotion)


def generate_dialogue(
    user_message: str,
    *,
    affinity: int = 0,
    chapter: int = 0,
    history: Optional[List[Dict[str, str]]] = None,
    tool_result: Optional[Dict[str, Any]] = None,
) -> DialogueResult:
    """최종 대사와 표정을 생성한다.

    Args:
        user_message: 유저 발화.
        affinity: 현재 호감도(말투 결정).
        chapter: 현재 챕터(맥락).
        history: 단기 메모리 대화 리스트(memory.store.get_short_term 결과).
        tool_result: tool_router가 반환한 도구 결과(항공권 등). 없으면 None.

    Returns:
        DialogueResult(dialogue_list, emotion_code). 실패 시에도 폴백으로 항상 유효한 결과.
    """
    history = history or []

    if not llm_client.is_available():
        return _fallback(user_message, affinity)

    messages = _build_messages(user_message, affinity, chapter, history, tool_result)
    try:
        raw = llm_client.chat(messages, temperature=0.8, max_tokens=512)
    except llm_client.LLMUnavailableError:
        return _fallback(user_message, affinity)

    parsed = _parse_llm_json(raw)
    if parsed is None:
        # JSON 파싱 실패: 원문을 한 줄 대사로라도 살려준다
        return DialogueResult(dialogue_list=[raw], emotion_code=_DEFAULT_EMOTION)
    return parsed
