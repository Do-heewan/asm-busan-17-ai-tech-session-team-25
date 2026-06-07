"""
게임 코어 API 라우터.

대화 턴 진행(/chat)과 세션 초기화(/reset)를 제공한다.
한 번의 /chat 호출이 다음 전체 턴 루프를 수행하고 프론트엔드 규격(TurnResult)으로 반환한다.

    메모리 로드 → 의도 분류(혜성) → 도구 호출(혜성) → 대사 생성(희완)
    → 호감도 갱신(희완) → 스토리 평가(희완) → 프로필/요약 메모리 갱신 → 저장

각 외부 의존(LLM·항공권 API·의도 분류기)은 키가 없거나 실패해도 안전 폴백하도록 감싸
어떤 상황에서도 게임 턴이 완결되게 한다.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.schemas.request import ChatRequest
from app.schemas.response import TurnResult
from app.memory import store
from app.agents import dialogue_generator, story_engine
from app.services import affinity_calculator

router = APIRouter()

# 의도 분류기/도구 라우터는 무거운(외부 SDK·네트워크) 객체이므로 지연 생성한다.
# 생성/호출 실패 시에도 파이프라인이 죽지 않도록 아래 헬퍼에서 폴백을 보장한다.
_classifier = None
_tool_router = None


def _classify_intent(user_message: str, chapter: int, affinity: int) -> Dict[str, Any]:
    """발화 의도를 분류한다(혜성 모듈). 사용 불가 시 'dialogue' 로 폴백."""
    global _classifier
    try:
        if _classifier is None:
            from app.agents.intent_classifier import IntentClassifier

            _classifier = IntentClassifier()
        return _classifier.classify(user_message, chapter, affinity)
    except Exception:
        return {"intent": "dialogue", "params": {}, "reason": "의도 분류기 사용 불가"}


def _route_tool(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """의도에 맞는 도구를 호출한다(혜성 모듈). 사용 불가 시 빈 결과로 폴백."""
    global _tool_router
    try:
        if _tool_router is None:
            from app.agents.tool_router import ToolRouter

            _tool_router = ToolRouter()
        return _tool_router.route(intent, params)
    except Exception:
        return {"tool_name": "none", "results": [], "summary": ""}


@router.post("/chat", response_model=TurnResult)
async def process_chat_turn(request: ChatRequest) -> TurnResult:
    """유저의 한 턴 입력을 받아 상태를 갱신하고 결과를 반환하는 코어 API."""

    # -------------------------------------------------------------------------
    # 1. 메모리 로드 (단기 대화 + 장기 요약/프로필/플래그)
    # -------------------------------------------------------------------------
    history = store.get_short_term(request.session_id)
    summary = store.get_summary(request.session_id)
    profile = store.get_profile(request.session_id)
    flags: Dict[str, Any] = dict(store.load_session(request.session_id)["long_term"]["flags"])

    # -------------------------------------------------------------------------
    # 2. 의도 분류 (대화 / 도구 / 선택)
    # -------------------------------------------------------------------------
    intent_obj = _classify_intent(
        request.user_message, request.current_chapter, request.current_affinity
    )
    intent = intent_obj.get("intent", "dialogue")

    # -------------------------------------------------------------------------
    # 3. 도구 호출 (의도가 'tool' 일 때만). 항공권 등 외부 결과를 tool_result 로.
    # -------------------------------------------------------------------------
    tool_result: Optional[Dict[str, Any]] = None
    if intent == "tool":
        routed = _route_tool("tool", intent_obj.get("params", {}))
        # 결과나 안내 메시지가 있으면 대사 생성기에 사실 근거로 전달
        if routed.get("results") or routed.get("summary"):
            tool_result = routed
        # 지연 항공편이 조회되면 지연 이벤트 플래그를 켠다(story_engine 가 탑승 게이트에서 사용).
        # NOTE: 현재 항공권 스키마에 지연 필드가 없으므로 'delayed' 키가 있을 때만 동작한다(추후 도구 보강 지점).
        if any(r.get("delayed") for r in routed.get("results", [])):
            flags["flight_delayed"] = True

    # -------------------------------------------------------------------------
    # 4. 최종 대사·표정 생성 (프로필/요약/도구결과 주입, 키 없으면 더미 폴백)
    # -------------------------------------------------------------------------
    dialogue = dialogue_generator.generate_dialogue(
        request.user_message,
        affinity=request.current_affinity,
        chapter=request.current_chapter,
        history=history,
        tool_result=tool_result,
        profile=profile,
        summary=summary,
    )

    # -------------------------------------------------------------------------
    # 5. 호감도 증감 연산 (생성된 감정 + 유저 발화 기반)
    # -------------------------------------------------------------------------
    affinity_delta, new_affinity = affinity_calculator.step(
        request.current_affinity,
        request.user_message,
        dialogue.emotion_code,
    )

    # -------------------------------------------------------------------------
    # 6. 스토리 평가 (씬 전환/엔딩/이벤트). flags 에 지연 플래그가 반영된다.
    # -------------------------------------------------------------------------
    decision = story_engine.evaluate(
        current_chapter=request.current_chapter,
        affinity=new_affinity,
        user_message=request.user_message,
        flags=flags,
    )

    # -------------------------------------------------------------------------
    # 7. 이번 턴 대화 저장 → 사용자 프로필 추출 → (전환 시) 요약 메모리 갱신
    # -------------------------------------------------------------------------
    store.append_turn(request.session_id, request.user_message, dialogue.dialogue_list)

    extracted_profile = dialogue_generator.extract_profile(request.user_message)

    new_summary: Optional[str] = None
    if decision.is_transition:
        # 방금 턴까지 반영된 단기 기록으로 이전 챕터를 요약·압축한다.
        updated_history = store.get_short_term(request.session_id)
        new_summary = dialogue_generator.generate_summary(updated_history, summary)

    # 켜진 플래그(이벤트 + 지연)를 한 번에 누적 저장
    flag_updates: Dict[str, Any] = {}
    if decision.event:
        flag_updates[decision.event] = True
    if flags.get("flight_delayed"):
        flag_updates["flight_delayed"] = True

    store.update_state(
        request.session_id,
        affinity=new_affinity,
        chapter=decision.next_chapter,
        flags=flag_updates or None,
        summary=new_summary,
        profile=extracted_profile or None,
    )

    # -------------------------------------------------------------------------
    # 8. 프론트엔드 규격(TurnResult)으로 응답
    # -------------------------------------------------------------------------
    return TurnResult(
        next_chapter=decision.next_chapter,
        affinity_delta=affinity_delta,
        agent_dialogue_list=dialogue.dialogue_list,
        emotion_code=dialogue.emotion_code,
        metadata={
            "is_transition": decision.is_transition,
            "is_ending": decision.is_ending,
            "event": decision.event,
            "current_affinity": new_affinity,
            "intent": intent,
            "tool_result": tool_result,
            **decision.metadata,
        },
    )


@router.post("/reset/{session_id}")
async def reset_session(session_id: str) -> dict:
    """세션 상태를 초기화한다(게임 다시 시작)."""
    store.reset_session(session_id)
    return {"status": "ok", "message": f"세션 '{session_id}'이(가) 초기화되었습니다."}
