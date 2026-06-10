# Affinity Rebalance — Design Spec

**Date:** 2026-06-11
**Branch:** feat/affinity-logic
**Status:** Approved

---

## 목표

현재 호감도가 정상 플레이에서 85+까지 치솟아 `ending_best`만 나오는 문제를 해결한다.
정상 플레이 → `ending_good(40~69)`, 적극적 플레이 → `ending_best(70+)`, 무관심 플레이 → `ending_solo(<40)`.

---

## 원인

1. **LLM 감정 편향**: `surprise` 정의에 "설렘"이 포함되어 여행 대화에서 매 턴 발동 → 매 턴 +2
2. **가중치 불균형**: `smile(+3)`, `surprise(+2)`가 관대하고 `sad(-3)`은 거의 발동 안 됨
3. **부정 키워드 부족**: 무관심·회피형 발화가 점수에 반영되지 않음

---

## 변경 파일 2개

### 1. `backend/app/prompts/system_prompts.py`

`OUTPUT_FORMAT` 내 emotion 설명 교체.

**현재:**
```
emotion: idle(평온/기본) | smile(기쁨/호감) | sad(서운함/실망) | surprise(놀람/설렘) 중 하나
```

**변경:**
```
emotion: 아래 중 하나. 일반 대화는 반드시 idle이 기본값.
- idle: 평온한 대화, 긍정적이지만 특별하지 않은 반응
- smile: 사용자가 특별히 다정하거나 애정 어린 말을 했을 때만
- sad: 사용자가 무관심하게 답하거나 부정적·짧은 반응을 보일 때
- surprise: 진짜 예상치 못한 발화일 때만 (설렘·흥분은 idle로 표현)
```

**핵심 변경 의도:**
- `surprise`에서 "설렘" 제거 → 여행 대화의 기본 흥분감은 `idle`로 흡수
- `idle`이 기본값임을 명시하여 LLM이 스팸성 `smile`/`surprise` 선택 억제

### 2. `backend/app/services/affinity_calculator.py`

#### 감정 가중치 조정

| emotion | 현재 | 변경 | 이유 |
|---|---|---|---|
| `smile` | +3 | **+2** | 자주 나오므로 영향 완화 |
| `surprise` | +2 | **+1** | 프롬프트 개선 후 안전망 |
| `idle` | 0 | **0** | 유지 |
| `sad` | -3 | **-3** | 유지 (잘 안 나오므로 강하게 유지) |

#### 부정 키워드 추가 (8개)

기존 12개에 무관심·회피형 키워드 추가:

| 키워드 | 분류 |
|---|---|
| `몰라` | 무관심 |
| `아무거나` | 무관심 |
| `상관없어` | 무관심 |
| `됐어` | 거절/포기 |
| `빼줘` | 거절 |
| `패스` | 회피 |
| `피곤해` | 무기력 |
| `졸려` | 무기력 |

---

## 기대 효과

시작 호감도 50, ~30턴 플레이 기준:

| 플레이 스타일 | 예상 최종 호감도 | 엔딩 |
|---|---|---|
| 무관심 (무관심 키워드, sad 유발) | 35~45 | `ending_solo` |
| 평범 (mostly idle, 짧은 답변) | 55~65 | `ending_good` |
| 적극 (smile 다수, 긍정 키워드) | 70+ | `ending_best` |

---

## 테스트 포인트

- `compute_delta("", "smile")` → `2` (기존 3에서 변경)
- `compute_delta("", "surprise")` → `1` (기존 2에서 변경)
- `compute_delta("몰라", "idle")` → `-3` (부정 키워드 반영)
- `compute_delta("아무거나 해줘", "idle")` → `-3`
- `compute_delta("좋아 고마워", "smile")` → 기존 keyword(+4 cap) + emotion(+2) 정상 작동 확인
- LLM 환경: 일반 대화에서 `idle` 비율 증가 수동 확인
