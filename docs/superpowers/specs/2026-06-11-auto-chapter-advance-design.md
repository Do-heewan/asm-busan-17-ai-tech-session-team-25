# Auto Chapter Advance (챕터 자동 전환) — Design Spec

**Date:** 2026-06-11
**Branch:** feat/flight-selection-ui
**Status:** Approved

---

## 목표

챕터 4 이상에서 해당 챕터의 대화 턴 수가 5 이상이 되면, 트리거 키워드 없이도 자동으로 다음 챕터로 전환한다. 전환 직전에 LLM이 상황에 맞는 자연스러운 유도 대사를 생성한다.

---

## 적용 범위

| 챕터 | 이름 | 자동 전환 대상 | 전환 대상 |
|------|------|:--------------:|-----------|
| 4 | 탑승 게이트 | ✅ | 챕터 5 (기내) |
| 5 | 기내 | ✅ | 챕터 6 (도착) |
| 6 | 도착 | ✅ | 엔딩 (99, 호감도 기준 분기) |
| 0~3 | 나머지 | ❌ | 기존 트리거 방식 유지 |

---

## 변경 파일

### 1. `backend/app/agents/story_engine.py`

`evaluate()` 내 기존 트리거 조건 평가 **이전**에 자동 전환 블록 삽입.

```python
# 자동 전환: 챕터 4 이상에서 5턴 초과 시
AUTO_ADVANCE_CHAPTER_THRESHOLD = 4
AUTO_ADVANCE_TURNS_THRESHOLD = 5

if (
    current_chapter >= AUTO_ADVANCE_CHAPTER_THRESHOLD
    and chapter_turns >= AUTO_ADVANCE_TURNS_THRESHOLD
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

**조건 순서 (우선순위):**
1. 특수 이벤트 판정 (`_check_event`) — 기존 유지
2. **자동 전환 조건** — 신규 (챕터>=4 AND turns>=5)
3. 트리거 기반 전환 — 기존 유지

### 2. `backend/app/agents/orchestrator.py`

`story_engine.evaluate()` 호출 후, nudge 신호를 `dialogue_generator`에 전달.

```python
nudge = decision.metadata.get("nudge", False)

dialogue = dialogue_generator.generate_dialogue(
    request.user_message,
    affinity=request.current_affinity,
    chapter=request.current_chapter,
    history=history,
    tool_result=tool_result,
    profile=profile,
    summary=summary,
    nudge_transition=nudge,   # 추가
)
```

### 3. `backend/app/agents/dialogue_generator.py`

`generate_dialogue()`에 `nudge_transition: bool = False` 파라미터 추가. `True`일 때 시스템 프롬프트 끝에 조건부 지시문 삽입.

```python
if nudge_transition:
    system_prompt += (
        "\n\n[전환 유도] 이번 대사에서 자연스럽게 다음 장면으로 넘어가는 흐름을 만들어. "
        "직접적으로 '가자'라고 말하지 말고, 캐릭터 말투에 맞게 상황을 마무리하는 뉘앙스를 담아."
    )
```

---

## 데이터 흐름

```
턴 시작
  └─ orchestrator: chapter_turns += 1, flags 갱신
       └─ story_engine.evaluate()
            ├─ _check_event() → event 판정
            ├─ [NEW] 챕터>=4 AND turns>=5?
            │     YES → StoryDecision(is_transition=True, nudge=True)
            │     NO  → 기존 트리거 판정 계속
            └─ StoryDecision 반환
       └─ decision.metadata["nudge"] == True?
            YES → dialogue_generator(nudge_transition=True)
                   → LLM: 전환 유도 대사 생성
            NO  → dialogue_generator(nudge_transition=False) (기존)
       └─ TurnResult(next_chapter=다음챕터) 반환 → 프론트엔드 전환
```

---

## 엣지 케이스

| 상황 | 처리 |
|------|------|
| 챕터 6 자동 전환 | `next_id=None` 분기 → `_decide_ending(affinity)` 호출, `ENDING_CHAPTER(99)` 반환 |
| 자동 전환과 트리거가 동시에 성립 | 자동 전환이 먼저 평가되므로 자동 전환 우선 |
| `chapter_turns` 리셋 | 기존 로직 유지 — 전환 시 `flag_updates["chapter_turns"] = 0` |
| `dialogue_generator` 시그니처 변경 | 기본값 `False`이므로 기존 호출부 변경 불필요 |

---

## 테스트 포인트

- `story_engine.evaluate()`: 챕터 4, turns=5 → `is_transition=True`, `nudge=True`
- `story_engine.evaluate()`: 챕터 4, turns=4 → `is_transition=False`
- `story_engine.evaluate()`: 챕터 3, turns=10 → `is_transition=False` (적용 대상 아님)
- `story_engine.evaluate()`: 챕터 6, turns=5 → `is_ending=True`, `next_chapter=99`
- `dialogue_generator.generate_dialogue()`: `nudge_transition=True` 시 프롬프트에 지시문 포함 확인
