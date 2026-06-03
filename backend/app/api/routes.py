from fastapi import APIRouter
from app.schemas.request import ChatRequest
from app.schemas.response import TurnResult

router = APIRouter()

@router.post("/chat", response_model=TurnResult)
async def process_chat_turn(request: ChatRequest):
    """
    유저의 한 턴 입력(대화/선택/도구 요청)을 받아 상태를 갱신하고 결과를 반환하는 코어 API입니다.
    이 엔드포인트 하나로 게임의 메인 턴 루프와 씬 전환을 모두 통제합니다.
    """
    
    # =========================================================================
    # 1. 입력 데이터 수신 및 역할 설명 (State Input)
    # =========================================================================
    # [request.session_id]
    #  - 유저별 고유 세션 키입니다. 백엔드 메모리 스토어(Memory Store)에서 
    #    해당 유저의 단기 대화 내역(6~8턴) 및 장기 플래그 데이터를 로드/저장할 때 식별자로 씁니다.
    #
    # [request.user_message]
    #  - 유저가 입력창에 친 실제 대사 텍스트입니다. 의도 분류기(Intent Classifier)와 
    #    감정 분석 모듈이 이 텍스트를 파싱하여 도구 호출이나 호감도 계산을 시작합니다.
    #
    # [request.current_chapter]
    #  - 현재 게임이 머물러 있는 상태(챕터 ID)입니다. (예: 'airport_waiting', 'paris_tour')
    #    이 값에 따라 스토리 엔진이 어떤 이벤트 조건을 평가할지 결정 기준이 됩니다.
    #
    # [request.current_affinity]
    #  - 프론트엔드에 저장되어 있던 현재 호감도 점수입니다. 대사 생성기(Dialogue Generator)가 
    #    캐릭터의 대사 수위나 친밀도 표현 톤앤매너를 결정할 때 참조합니다.
    # =========================================================================


    # -------------------------------------------------------------------------
    # [개발 참고] 추후 구현될 실제 에이전틱 워크플로우(Agentic Workflow) 파이프라인 흐름:
    # 1. intent = intent_classifier.py(request.user_message) -> 의도 파악 (대화/도구/선택)
    # 2. if intent == "도구": tool_result = tool_router.py(...) -> Amadeus API 등 호출
    # 3. affinity_delta = affinity_calculator.py(...) -> 호감도 변동 연산
    # 4. final_dialogue, emotion = dialogue_generator.py(...) -> 최종 대사 및 표정 확정
    # 5. is_trigger, next_chapter = story_engine.py(...) -> 현재 상태 기준 씬 종료 조건 평가
    # -------------------------------------------------------------------------


    # =========================================================================
    # 2. 임시 가상 분기 로직 (UI 개발용 Dummy Logic)
    # =========================================================================
    # 프론트엔드에서 '예약' 또는 '출발'이라는 단어를 입력하면 
    # 조건이 충족되어 다음 씬으로 전환되는 시뮬레이션을 구현했습니다.
    is_trigger = any(keyword in request.user_message for keyword in ["예약", "출발", "가자"])
    
    
    # =========================================================================
    # 3. 최종 상태 반환 및 역할 설명 (State Output)
    # =========================================================================
    return TurnResult(
        # [next_scene_trigger]
        #  - 핵심 전환 플래그입니다. True가 내려가면 프론트엔드는 즉시 유저 입력창을 막고,
        #    화면 페이드아웃 및 다음 챕터 연출(일러스트 교체 등)을 수행해야 함을 인지합니다.
        next_scene_trigger=is_trigger,
        
        # [current_chapter]
        #  - 유저가 계속 진행하게 될 챕터의 ID입니다.
        #    next_scene_trigger가 True일 때는 전환될 '새 챕터 ID'가 되며, False일 때는 기존 챕터가 유지됩니다.
        current_chapter=request.current_chapter if not is_trigger else "flight_boarding",
        
        # [affinity_delta]
        #  - 이번 턴 유저의 말에 메이트가 반응하여 변화한 호감도 수치입니다. (예: +5, -2 등)
        #    프론트엔드는 상단 게이지 바를 이 수치만큼 애니메이션 효과와 함께 실시간으로 늘리거나 줄입니다.
        affinity_delta=3 if "좋아" in request.user_message else 1,
        
        # [agent_dialogue]
        #  - 화면 대화창에 타이핑 효과로 띄워줄 캐릭터의 실제 대사 내용입니다.
        agent_dialogue=f"응? 방금 '{request.user_message}'라고 했어? ㅎㅎ 너랑 같이 계획 짜니까 뭘 해도 다 재밌는 것 같아!",
        
        # [emotion_code]
        #  - 현재 메이트의 감정 상태를 뜻하는 약속된 코드명입니다.
        #    프론트엔드는 이 코드를 읽고 캐릭터 이미지 컴포넌트(CharacterSprite.tsx)의 소스 파일명을 매핑하여 표정을 바꿉니다.
        emotion_code="smile" if not is_trigger else "surprise",
        
        # [metadata]
        #  - 규격화되지 않은 자유 패턴 JSON 바구니입니다. 
        #    실제 항공권 리스트 데이터(`flight_data: [...]`)나 미션 달성 힌트 등 유동적인 컨텍스트를 담아 프론트에 공유합니다.
        metadata={
            "is_dummy": True,
            "received_session": request.session_id,
            "system_hint": "대화창에 '예약' 혹은 '출발'을 입력하면 다음 씬으로 넘어가는 연출을 테스트할 수 있습니다."
        }
    )