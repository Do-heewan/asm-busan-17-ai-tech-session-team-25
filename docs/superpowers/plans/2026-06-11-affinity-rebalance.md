# Affinity Rebalance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 정상 플레이 시 호감도가 ending_good(40~69) 범위에서 마무리되도록 감정 가중치, 부정 키워드, LLM 감정 정의를 조정한다.

**Architecture:** `affinity_calculator.py`에서 `_EMOTION_WEIGHT`와 `_NEGATIVE_KEYWORDS`를 수정하고, `system_prompts.py`의 `OUTPUT_FORMAT` 감정 설명을 교체한다.

**Tech Stack:** Python 3.11, pytest

---

## File Map

| 파일 | 변경 내용 |
|------|-----------|
| `backend/tests/test_affinity_calculator.py` | 신규 — 가중치·키워드 단위 테스트 |
| `backend/app/services/affinity_calculator.py` | `_EMOTION_WEIGHT` 수치 변경 + `_NEGATIVE_KEYWORDS` 8개 추가 |
| `backend/app/prompts/system_prompts.py` | `OUTPUT_FORMAT` emotion 설명 교체 |

---

## Task 1: affinity_calculator 가중치 + 키워드 수정

**Files:**
- Create: `backend/tests/test_affinity_calculator.py`
- Modify: `backend/app/services/affinity_calculator.py:19-24` (가중치), `backend/app/services/affinity_calculator.py:31-34` (키워드)

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_affinity_calculator.py`:

```python
from app.services.affinity_calculator import compute_delta, _keyword_score

# ---------------------------------------------------------------------------
# 감정 가중치 변경 확인
# ---------------------------------------------------------------------------

def test_smile_weight_is_2():
    """smile 가중치가 2여야 한다 (기존 3에서 변경)."""
    assert compute_delta("", "smile") == 2


def test_surprise_weight_is_1():
    """surprise 가중치가 1이어야 한다 (기존 2에서 변경)."""
    assert compute_delta("", "surprise") == 1


def test_idle_weight_unchanged():
    """idle 가중치는 0 유지."""
    assert compute_delta("", "idle") == 0


def test_sad_weight_unchanged():
    """sad 가중치는 -3 유지."""
    assert compute_delta("", "sad") == -3


# ---------------------------------------------------------------------------
# 신규 부정 키워드 확인
# ---------------------------------------------------------------------------

def test_keyword_molla():
    """'몰라' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("몰라") == -3


def test_keyword_amuguna():
    """'아무거나' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("아무거나") == -3


def test_keyword_sangkwan_eopseo():
    """'상관없어' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("상관없어") == -3


def test_keyword_dwaesseo():
    """'됐어' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("됐어") == -3


def test_keyword_bbaeJwo():
    """'빼줘' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("빼줘") == -3


def test_keyword_pass():
    """'패스' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("패스") == -3


def test_keyword_pigonhae():
    """'피곤해' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("피곤해") == -3


def test_keyword_jollyeo():
    """'졸려' 발화는 -3 점수를 반환한다."""
    assert _keyword_score("졸려") == -3


# ---------------------------------------------------------------------------
# 복합: 긍정 키워드 + smile 감정
# ---------------------------------------------------------------------------

def test_positive_keyword_with_smile():
    """'좋아 고마워' + smile: 키워드(+4 cap) + emotion(+2) = 6."""
    assert compute_delta("좋아 고마워", "smile") == 6


# ---------------------------------------------------------------------------
# 복합: 부정 키워드 + idle 감정
# ---------------------------------------------------------------------------

def test_negative_keyword_molla_with_idle():
    """'몰라' + idle: 키워드(-3) + emotion(0) = -3."""
    assert compute_delta("몰라", "idle") == -3
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd backend
python -m pytest tests/test_affinity_calculator.py -v
```

Expected: `smile` weight 테스트 → `assert 3 == 2` FAIL, 신규 키워드 테스트 → `assert 0 == -3` FAIL

- [ ] **Step 3: 가중치 수정**

`backend/app/services/affinity_calculator.py:19-24`의 `_EMOTION_WEIGHT`를 아래로 교체:

```python
_EMOTION_WEIGHT: Dict[str, int] = {
    "smile": 2,
    "surprise": 1,
    "idle": 0,
    "sad": -3,
}
```

- [ ] **Step 4: 부정 키워드 추가**

`backend/app/services/affinity_calculator.py:31-34`의 `_NEGATIVE_KEYWORDS`를 아래로 교체:

```python
_NEGATIVE_KEYWORDS = (
    "싫어", "별로", "짜증", "그만", "관심없", "노잼", "최악", "꺼져",
    "바보", "멍청", "지겨", "귀찮",
    "몰라", "아무거나", "상관없어", "됐어", "빼줘", "패스", "피곤해", "졸려",
)
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd backend
python -m pytest tests/test_affinity_calculator.py -v
```

Expected: 14개 모두 PASS

- [ ] **Step 6: 전체 테스트 회귀 확인**

```bash
cd backend
python -m pytest tests/ -v
```

Expected: 23개 모두 PASS (기존 9 + 신규 14)

- [ ] **Step 7: 커밋**

```bash
git add backend/tests/test_affinity_calculator.py backend/app/services/affinity_calculator.py
git commit -m "feat(affinity): rebalance emotion weights and add disengagement keywords"
```

---

## Task 2: system_prompts emotion 정의 교체

**Files:**
- Modify: `backend/app/prompts/system_prompts.py:61-68`

> 이 변경은 LLM 동작에 영향을 주므로 자동 테스트 대신 문자열 포함 여부 단위 테스트로 검증한다.

- [ ] **Step 1: 실패하는 테스트 작성**

`backend/tests/test_affinity_calculator.py` 끝에 추가:

```python
# ---------------------------------------------------------------------------
# system_prompts OUTPUT_FORMAT 감정 정의 확인
# ---------------------------------------------------------------------------
from app.prompts.system_prompts import OUTPUT_FORMAT

def test_output_format_idle_is_default():
    """OUTPUT_FORMAT에 idle이 기본값임이 명시되어야 한다."""
    assert "기본값" in OUTPUT_FORMAT


def test_output_format_surprise_excludes_excitement():
    """OUTPUT_FORMAT에서 surprise가 설렘을 포함하지 않아야 한다."""
    assert "설렘" not in OUTPUT_FORMAT


def test_output_format_sad_includes_disengagement_cue():
    """OUTPUT_FORMAT에서 sad가 무관심 반응에 대한 안내를 포함해야 한다."""
    assert "무관심" in OUTPUT_FORMAT
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd backend
python -m pytest tests/test_affinity_calculator.py::test_output_format_idle_is_default tests/test_affinity_calculator.py::test_output_format_surprise_excludes_excitement tests/test_affinity_calculator.py::test_output_format_sad_includes_disengagement_cue -v
```

Expected: 3개 모두 FAIL

- [ ] **Step 3: OUTPUT_FORMAT 교체**

`backend/app/prompts/system_prompts.py`의 `OUTPUT_FORMAT` 변수 전체를 아래로 교체:

```python
OUTPUT_FORMAT = """[출력 형식]
반드시 아래 JSON 형식 하나만 출력한다. 코드블록(```)·주석(//)·다른 설명은 절대 덧붙이지 않는다.
{
  "dialogue": ["말풍선1", "말풍선2"],
  "emotion": "smile"
}
- dialogue: 1~3개의 짧은 대사 문자열 배열
- emotion: 아래 중 하나. 일반 대화는 반드시 idle이 기본값.
  - idle: 평온한 대화, 긍정적이지만 특별하지 않은 반응
  - smile: 사용자가 특별히 다정하거나 애정 어린 말을 했을 때만
  - sad: 사용자가 무관심하게 답하거나 부정적·짧은 반응을 보일 때
  - surprise: 진짜 예상치 못한 발화일 때만 (설렘·흥분은 idle로 표현)"""
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd backend
python -m pytest tests/test_affinity_calculator.py -v
```

Expected: 17개 모두 PASS

- [ ] **Step 5: 전체 테스트 회귀 확인**

```bash
cd backend
python -m pytest tests/ -v
```

Expected: 26개 모두 PASS

- [ ] **Step 6: 커밋**

```bash
git add backend/tests/test_affinity_calculator.py backend/app/prompts/system_prompts.py
git commit -m "feat(prompts): tighten emotion definitions to reduce surprise/smile bias"
```

---

## 완료 기준

- [ ] `pytest tests/` 26개 모두 PASS
- [ ] `compute_delta("", "smile")` == 2, `compute_delta("", "surprise")` == 1
- [ ] `_keyword_score("몰라")` == -3
- [ ] `OUTPUT_FORMAT`에 "설렘" 미포함, "무관심" 포함, "기본값" 포함
- [ ] LLM 환경에서 일반 대화 시 `idle` 비율 증가 수동 확인
