from app.agents.dialogue_generator import _build_messages

NUDGE_KEYWORD = "자연스럽게 다음 장면으로 넘어가는"


def test_build_messages_nudge_injects_instruction():
    """nudge_transition=True 이면 system 메시지에 전환 유도 지시문이 포함된다."""
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
