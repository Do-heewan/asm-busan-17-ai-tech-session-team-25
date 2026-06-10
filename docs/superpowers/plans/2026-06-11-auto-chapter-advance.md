# Auto Chapter Advance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 챕터 4 이상에서 `chapter_turns >= 5`이 되면 트리거 없이 자동으로 다음 챕터로 전환하고, LLM이 자연스러운 전환 유도 대사를 생성한다.

**Architecture:** `story_engine.evaluate()`에 자동 전환 조건 블록 추가 → `orchestrator`가 `nudge` 플래그를 감지해 `dialogue_generator`에 전달 → `dialogue_generator`가 nudge 지시문을 시스템 프롬프트에 삽입.

**Tech Stack:** Python 3.11, pytest, FastAPI (변경 없음)

---

## File Map

| 파일 | 변경 내용 |
|------|-----------|
| `backend/requirements.txt` | pytest 추가 |
| `backend/tests/__init__.py` | 신규 생성 (빈 파일) |
| `backend/tests/test_story_engine.py` | 신규 — story_engine 자동 전환 단위 테스트 |
| `backend/tests/test_dialogue_generator.py` | 신규 — nudge 프롬프트 삽입 단위 테스트 |
| `backend/app/agents/story_engine.py` | 자동 전환 상수 + evaluate() 블록 추가 |
| `backend/app/agents/dialogue_generator.py` | `generate_dialogue(nudge_transition)` 파라미터 + `_build_messages` 수정 |
| `backend/app/agents/orchestrator.py` | nudge 감지 후 `dialogue_generator` 호출 시 전달 |

---

## Task 1: 테스트 인프라 + story_engine 자동 전환 구현

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_story_engine.py`
- Modify: `backend/app/agents/story_engine.py`

- [ ] **Step 1: pytest를 requirements.txt에 추가**

`backend/requirements.txt` 끝에 한 줄 추가:

```
pytest>=8.0.0
```

- [ ] **Step 2: tests 패키지 초기화 파일 생성**

`backend/tests/__init__.py` 를 빈 파일로 생성한다.

- [ ] **Step 3: 실패하는 테스트 작성**

`backend/tests/test_story_engine.py`:

```python
import pytest
from app.agents.story_engine import evaluate, STORY_LINE

# ---------------------------------------------------------------------------
# 자동 전환 — 챕터 4 이상, turns >= 5
# ---------------------------------------------------------------------------

def test_auto_advance_chapter4_at_turn5():
    """챕터 4에서 chapter_turns == 5이면 챕터 5로 자동 전환된다."""
    decision = evaluate(
        current_chapter=4,
        affinity=50,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.is_transition is True
    assert decision.next_chapter == 5
    assert decision.metadata.get("nudge") is True


def test_auto_advance_chapter4_turn4_does_not_fire():
    """챕터 4에서 chapter_turns == 4이면 자동 전환되지 않는다."""
    decision = evaluate(
        current_chapter=4,
        affinity=50,
        user_message="",
        flags={"chapter_turns": 4},
    )
    assert decision.is_transition is False
    assert decision.next_chapter == 4


def test_auto_advance_chapter5_at_turn5():
    """챕터 5에서 chapter_turns == 5이면 챕터 6으로 자동 전환된다."""
    decision = evaluate(
        current_chapter=5,
        affinity=50,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.is_transition is True
    assert decision.next_chapter == 6
    assert decision.metadata.get("nudge") is True


def test_auto_advance_chapter6_ending_best():
    """챕터 6에서 chapter_turns == 5, 호감도 >= 70이면 엔딩(99)으로 자동 전환된다."""
    decision = evaluate(
        current_chapter=6,
        affinity=70,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.is_transition is True
    assert decision.is_ending is True
    assert decision.next_chapter == 99
    assert decision.metadata.get("nudge") is True
    assert decision.metadata.get("ending") == "ending_best"


def test_auto_advance_chapter6_ending_good():
    """챕터 6에서 호감도 40~69이면 ending_good."""
    decision = evaluate(
        current_chapter=6,
        affinity=50,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.metadata.get("ending") == "ending_good"


def test_auto_advance_chapter6_ending_solo():
    """챕터 6에서 호감도 < 40이면 ending_solo."""
    decision = evaluate(
        current_chapter=6,
        affinity=30,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.metadata.get("ending") == "ending_solo"


def test_auto_advance_does_not_apply_to_chapter3():
    """챕터 3은 자동 전환 대상이 아니다 — turns가 아무리 많아도 트리거 없으면 유지."""
    decision = evaluate(
        current_chapter=3,
        affinity=50,
        user_message="",
        flags={"chapter_turns": 99},
    )
    assert decision.is_transition is False
    assert decision.next_chapter == 3
```

- [ ] **Step 4: 테스트 실패 확인 (터미널에서 실행)**

```bash
cd backend
pytest tests/test_story_engine.py -v
```

Expected: `NameError` 또는 `AssertionError` — `nudge` 키가 없거나 자동 전환이 없으므로 실패

- [ ] **Step 5: story_engine.py 구현**

`backend/app/agents/story_engine.py` 에서 상수 2개 추가 후, `evaluate()` 안 이벤트 판정 직후에 자동 전환 블록 삽입.

**상수 추가 — 파일 상단 `_GATE_CHAPTER = 4` 아래:**

```python
# 자동 전환이 적용되는 최소 챕터 ID (이 값 이상의 챕터에 적용)
AUTO_ADVANCE_MIN_CHAPTER = 4
# 자동 전환을 발동하는 최소 챕터 내 턴 수
AUTO_ADVANCE_TURNS = 5
```

**`evaluate()` 함수 — 이벤트 판정(`event = _check_event(...)`) 직후, 기존 트리거 조건(`keyword_triggered = ...`) 이전에 삽입:**

```python
    # 자동 전환: 챕터 AUTO_ADVANCE_MIN_CHAPTER 이상에서 turns >= AUTO_ADVANCE_TURNS
    if (
        current_chapter >= AUTO_ADVANCE_MIN_CHAPTER
        and chapter_turns >= AUTO_ADVANCE_TURNS
    ):
        if chapter.next_id is None:
            ending_code = _decide_ending(affinity)
            return StoryDecision(
                next_chapter=ENDING_CHAPTER,
                is_transition=True,
                is_ending=True,
                event=event,
                metadata={"nudge": True, "ending": ending_code, "final_affinity": affinity},
            )
        next_ch = STORY_LINE[chapter.next_id]
        return StoryDecision(
            next_chapter=next_ch.id,
            is_transition=True,
            event=event,
            metadata={"nudge": True, "from": chapter.name, "to": next_ch.name},
        )
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
cd backend
pytest tests/test_story_engine.py -v
```

Expected: 7개 모두 PASS

- [ ] **Step 7: 커밋**

```bash
git add backend/requirements.txt backend/tests/__init__.py backend/tests/test_story_engine.py backend/app/agents/story_engine.py
git commit -m "feat(story): auto-advance chapter 4+ after 5 turns"
```

---

## Task 2: dialogue_generator nudge_transition 파라미터 추가

**Files:**
- Create: `backend/tests/test_dialogue_generator.py`
- Modify: `backend/app/agents/dialogue_generator.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_dialogue_generator.py`:

```python
from app.agents.dialogue_generator import _build_messages

NUDGE_KEYWORD = "자연스럽게 다음 장면으로 넘어가는"


def test_build_messages_nudge_injects_instruction():
    """nudge_transition=True 이면 마지막 system 메시지에 전환 유도 지시문이 포함된다."""
    messages = _build_messages(
        user_message="테스트",
        affinity=50,
        chapter=4,
        history=[],
        tool_result=None,
        nudge_transition=True,
    )
    system_contents = [m["content"] for m in messages if m["role"] == "system"]
    assert any(NUDGE_KEYWORD in c for c in system_contents), (
        f"nudge 지시문이 system 메시지에 없음. system 메시지: {system_contents}"
    )


def test_build_messages_no_nudge_has_no_instruction():
    """nudge_transition=False(기본값)이면 전환 유도 지시문이 없다."""
    messages = _build_messages(
        user_message="테스트",
        affinity=50,
        chapter=4,
        history=[],
        tool_result=None,
        nudge_transition=False,
    )
    system_contents = [m["content"] for m in messages if m["role"] == "system"]
    assert not any(NUDGE_KEYWORD in c for c in system_contents)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd backend
pytest tests/test_dialogue_generator.py -v
```

Expected: `TypeError` — `_build_messages`에 `nudge_transition` 파라미터 없으므로 실패

- [ ] **Step 3: `_build_messages` 시그니처 및 nudge 주입 구현**

`backend/app/agents/dialogue_generator.py` 의 `_build_messages` 함수:

```python
def _build_messages(
    user_message: str,
    affinity: int,
    chapter: int,
    history: List[Dict[str, str]],
    tool_result: Optional[Dict[str, Any]],
    profile: Optional[Dict[str, Any]] = None,
    summary: str = "",
    nudge_transition: bool = False,          # 추가
) -> List[Dict[str, str]]:
    """LLM에 보낼 messages 배열을 조립한다."""
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": build_system_prompt(affinity, chapter, profile=profile, summary=summary),
        }
    ]
    messages.extend(FEW_SHOT_EXAMPLES)
    messages.extend(history)

    if tool_result:
        messages.append(
            {
                "role": "system",
                "content": (
                    "[도구 조회 결과] 항공편 검색 결과가 있다. "
                    "결과 상세(가격·편명·시간)는 UI가 직접 표시하므로 절대 나열하지 말 것. "
                    "몇 개 찾았는지 + 골라보라는 짧은 한 줄 대사만 생성할 것.\n"
                    + json.dumps(tool_result, ensure_ascii=False)
                ),
            }
        )

    if nudge_transition:                      # 추가
        messages.append(
            {
                "role": "system",
                "content": (
                    "[장면 전환 유도] 이번 대사에서 자연스럽게 다음 장면으로 넘어가는 "
                    "흐름을 만들어. '가자'처럼 직접적으로 말하지 말고, "
                    "캐릭터 말투에 맞게 상황을 마무리하는 뉘앙스를 담아."
                ),
            }
        )

    messages.append({"role": "user", "content": user_message})
    return messages
```

- [ ] **Step 4: `generate_dialogue` 시그니처에 파라미터 추가**

`backend/app/agents/dialogue_generator.py` 의 `generate_dialogue` 함수 시그니처와 내부 `_build_messages` 호출:

```python
def generate_dialogue(
    user_message: str,
    *,
    affinity: int = 50,
    chapter: int = 0,
    history: Optional[List[Dict[str, str]]] = None,
    tool_result: Optional[Dict[str, Any]] = None,
    profile: Optional[Dict[str, Any]] = None,
    summary: str = "",
    nudge_transition: bool = False,          # 추가
) -> DialogueResult:
    history = history or []

    if not llm_client.is_available():
        return _fallback(user_message, affinity)

    messages = _build_messages(
        user_message, affinity, chapter, history, tool_result, profile, summary,
        nudge_transition=nudge_transition,   # 추가
    )
    # ... 이하 기존 코드 동일
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd backend
pytest tests/test_dialogue_generator.py -v
```

Expected: 2개 모두 PASS

- [ ] **Step 6: 전체 테스트 회귀 확인**

```bash
cd backend
pytest tests/ -v
```

Expected: 9개 모두 PASS

- [ ] **Step 7: 커밋**

```bash
git add backend/tests/test_dialogue_generator.py backend/app/agents/dialogue_generator.py
git commit -m "feat(dialogue): add nudge_transition param for auto-advance cue"
```

---

## Task 3: orchestrator nudge 신호 전달 배선

**Files:**
- Modify: `backend/app/agents/orchestrator.py:92-100`

> orchestrator는 외부 네트워크 의존성이 많아 단위 테스트 대신 기존 통합 경로(수동 실행)로 검증한다.

- [ ] **Step 1: orchestrator.py 수정**

`orchestrator.py` 의 `run_turn` 내 `dialogue_generator.generate_dialogue()` 호출 앞에 nudge 플래그 추출을 추가하고, 호출 시 전달한다.

`# 4. 대사·표정 생성` 블록을 아래와 같이 교체:

```python
        # ------------------------------------------------------------------ #
        # 4. 대사·표정 생성
        # ------------------------------------------------------------------ #
        nudge = decision.metadata.get("nudge", False)       # 추가
        dialogue = dialogue_generator.generate_dialogue(
            request.user_message,
            affinity=request.current_affinity,
            chapter=request.current_chapter,
            history=history,
            tool_result=tool_result,
            profile=profile,
            summary=summary,
            nudge_transition=nudge,                          # 추가
        )
```

단, `decision`은 현재 6번 스텝(스토리 평가) 뒤에 정의된다. `dialogue_generator` 호출이 4번 스텝에 있어 **`decision`이 아직 없는 문제**가 있으므로, 두 블록의 순서를 바꾼다:

**최종 순서 (orchestrator.py run_turn 내부):**

```
1. 메모리 로드
2. 의도 분류
2-b. chapter_turns 증가
3. 도구 호출
──────────────────────────── 순서 변경 ──────────────────────────────
4. [이동] 스토리 평가       (기존 6번) → decision/nudge 확보
5. [이동] 대사·표정 생성    (기존 4번, nudge 전달)
6. [이동] 호감도 증감 연산  (기존 5번, emotion_code 확정 후 계산)
──────────────────────────────────────────────────────────────────────
7. 메모리 갱신
8. TurnResult 반환
```

`backend/app/agents/orchestrator.py` 의 `run_turn` 메서드 전체를 아래로 교체:

```python
    def run_turn(self, request: ChatRequest) -> TurnResult:
        # 1. 메모리 로드
        history = store.get_short_term(request.session_id)
        summary = store.get_summary(request.session_id)
        profile = store.get_profile(request.session_id)
        flags: Dict[str, Any] = dict(
            store.load_session(request.session_id)["long_term"]["flags"]
        )

        # 2. 의도 분류
        intent_obj = self._classify_intent(
            request.user_message, request.current_chapter, request.current_affinity
        )
        intent = intent_obj.get("intent", "dialogue")

        # 2-b. 챕터 내 턴 카운터 증가
        chapter_turns = flags.get("chapter_turns", 0) + 1
        flags["chapter_turns"] = chapter_turns

        # 3. 도구 호출
        tool_result: Optional[Dict[str, Any]] = None
        if intent == "tool":
            routed = self._route_tool("tool", intent_obj.get("params", {}))
            if routed.get("results") or routed.get("summary"):
                tool_result = routed
            if any(r.get("delayed") for r in routed.get("results", [])):
                flags["flight_delayed"] = True

        # 4. 스토리 평가 (current_affinity 기준 — emotion_code는 아직 미확정)
        llm_triggered = dialogue_generator.check_transition_intent(
            chapter=request.current_chapter,
            user_message=request.user_message,
            history=history,
        )
        decision = story_engine.evaluate(
            current_chapter=request.current_chapter,
            affinity=request.current_affinity,
            user_message=request.user_message,
            flags=flags,
            llm_triggered=llm_triggered,
        )

        # 5. 대사·표정 생성 (nudge 플래그 전달)
        nudge = decision.metadata.get("nudge", False)
        dialogue = dialogue_generator.generate_dialogue(
            request.user_message,
            affinity=request.current_affinity,
            chapter=request.current_chapter,
            history=history,
            tool_result=tool_result,
            profile=profile,
            summary=summary,
            nudge_transition=nudge,
        )

        # 6. 호감도 증감 연산 (emotion_code 확정 후)
        affinity_delta, new_affinity = affinity_calculator.step(
            request.current_affinity,
            request.user_message,
            dialogue.emotion_code,
        )

        # 7. 메모리 갱신
        if not dialogue.is_fallback:
            store.append_turn(request.session_id, request.user_message, dialogue.dialogue_list)

        extracted_profile = dialogue_generator.extract_profile(request.user_message)

        new_summary: Optional[str] = None
        if decision.is_transition:
            updated_history = store.get_short_term(request.session_id)
            new_summary = dialogue_generator.generate_summary(updated_history, summary)

        flag_updates: Dict[str, Any] = {}
        if decision.event:
            flag_updates[decision.event] = True
        if flags.get("flight_delayed"):
            flag_updates["flight_delayed"] = True
        flag_updates["chapter_turns"] = 0 if decision.is_transition else chapter_turns

        store.update_state(
            request.session_id,
            affinity=new_affinity,
            chapter=decision.next_chapter,
            flags=flag_updates or None,
            summary=new_summary,
            profile=extracted_profile or None,
        )

        # 8. TurnResult 반환
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
```

- [ ] **Step 2: 전체 테스트 회귀 확인**

```bash
cd backend
pytest tests/ -v
```

Expected: 9개 모두 PASS

- [ ] **Step 3: 커밋**

```bash
git add backend/app/agents/orchestrator.py
git commit -m "feat(orchestrator): pass nudge flag to dialogue_generator for auto-advance"
```

---

## 완료 기준

- [ ] `pytest tests/` 9개 모두 PASS
- [ ] 챕터 4 이상에서 5턴 이후 `TurnResult.next_chapter`가 현재보다 높은 값으로 변경됨
- [ ] 해당 대사에 전환 유도 뉘앙스가 포함됨 (LLM 환경 기준 수동 확인)
