"""
게임 코어 API 라우터.

대화 턴 진행(/chat)과 세션 초기화(/reset)를 제공한다.
한 번의 /chat 호출이 메모리 로드 → 대사 생성 → 호감도 갱신 → 스토리 평가 →
메모리 저장의 전체 턴 루프를 수행하고, 프론트엔드 규격(TurnResult)으로 반환한다.

[향후 통합 예정 — 타 담당자 모듈]
  - intent_classifier(혜성): 발화 의도(대화/도구/선택) 분기
  - tool_router(혜성): Amadeus 항공권 등 외부 도구 호출 → tool_result
  - orchestrator(재혁): 아래 파이프라인을 총괄하는 상위 오케스트레이션 계층
현재는 위 모듈이 미구현이므로, 대화 중심 파이프라인으로 동작하며 도구 결과는 None이다.
"""

from fastapi import APIRouter

from app.schemas.request import ChatRequest
from app.schemas.response import TurnResult
from app.memory import store
from app.agents import dialogue_generator, story_engine
from app.services import affinity_calculator

router = APIRouter()


@router.post("/chat", response_model=TurnResult)
async def process_chat_turn(request: ChatRequest) -> TurnResult:
    """유저의 한 턴 입력을 받아 상태를 갱신하고 결과를 반환하는 코어 API."""

    # -------------------------------------------------------------------------
    # 1. 단기 메모리(이전 대화 맥락) 로드
    # -------------------------------------------------------------------------
    history = store.get_short_term(request.session_id)

    # -------------------------------------------------------------------------
    # 2. (TODO) 의도 분류 & 도구 호출
    #    intent = intent_classifier.classify(request.user_message)
    #    tool_result = tool_router.route(intent, ...) if intent == "도구" else None
    # -------------------------------------------------------------------------
    tool_result = None

    # -------------------------------------------------------------------------
    # 3. 최종 대사·표정 생성 (Solar LLM, 키 없으면 더미 폴백)
    # -------------------------------------------------------------------------
    dialogue = dialogue_generator.generate_dialogue(
        request.user_message,
        affinity=request.current_affinity,
        chapter=request.current_chapter,
        history=history,
        tool_result=tool_result,
    )

    # -------------------------------------------------------------------------
    # 4. 호감도 증감 연산 (생성된 감정 + 유저 발화 기반)
    # -------------------------------------------------------------------------
    affinity_delta, new_affinity = affinity_calculator.step(
        request.current_affinity,
        request.user_message,
        dialogue.emotion_code,
    )

    # -------------------------------------------------------------------------
    # 5. 스토리 평가 (씬 전환/엔딩/이벤트)
    # -------------------------------------------------------------------------
    session = store.load_session(request.session_id)
    decision = story_engine.evaluate(
        current_chapter=request.current_chapter,
        affinity=new_affinity,
        user_message=request.user_message,
        flags=session["long_term"]["flags"],
    )

    # -------------------------------------------------------------------------
    # 6. 메모리 저장 (이번 턴 대화 + 갱신된 장기 상태)
    # -------------------------------------------------------------------------
    store.append_turn(request.session_id, request.user_message, dialogue.dialogue_list)
    new_flags = {decision.event: True} if decision.event else None
    store.update_state(
        request.session_id,
        affinity=new_affinity,
        chapter=decision.next_chapter,
        flags=new_flags,
    )

    # -------------------------------------------------------------------------
    # 7. 프론트엔드 규격(TurnResult)으로 응답
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
            **decision.metadata,
        },
    )


@router.post("/reset/{session_id}")
async def reset_session(session_id: str) -> dict:
    """세션 상태를 초기화한다(게임 다시 시작)."""
    store.reset_session(session_id)
    return {"status": "ok", "message": f"세션 '{session_id}'이(가) 초기화되었습니다."}
