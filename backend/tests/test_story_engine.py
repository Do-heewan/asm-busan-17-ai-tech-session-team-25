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
    """챕터 6에서 chapter_turns == 5, 호감도 >= 90이면 엔딩(99)으로 자동 전환된다."""
    decision = evaluate(
        current_chapter=6,
        affinity=90,
        user_message="",
        flags={"chapter_turns": 5},
    )
    assert decision.is_transition is True
    assert decision.is_ending is True
    assert decision.next_chapter == 99
    assert decision.metadata.get("nudge") is True
    assert decision.metadata.get("ending") == "ending_best"


def test_auto_advance_chapter6_ending_good():
    """챕터 6에서 호감도 40~89이면 ending_good."""
    decision = evaluate(
        current_chapter=6,
        affinity=70,
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
