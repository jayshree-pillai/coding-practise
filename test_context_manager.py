from context_manager import build_context


def test_keeps_recent_history():
    history = [
        {
            "user": "old question",
            "assistant": "old answer",
        },
        {
            "user": "recent question",
            "assistant": "recent answer",
        },
    ]

    result = build_context(
        system_message="You are helpful",
        history=history,
        current_question="new question",
        token_budget=9,
    )

    contents = [message["content"] for message in result]

    assert "recent question" in contents
    assert "recent answer" in contents
    assert "old question" not in contents


def test_current_question_is_always_present():
    result = build_context(
        system_message="You are helpful",
        history=[],
        current_question="important current question",
        token_budget=4,
    )

    assert result[-1] == {
        "role": "user",
        "content": "important current question",
    }


def test_preserves_complete_turns():
    history = [
        {
            "user": "hello there",
            "assistant": "hello back",
        }
    ]

    result = build_context(
        system_message="System",
        history=history,
        current_question="next",
        token_budget=3,
    )

    roles = [message["role"] for message in result]

    assert roles == ["system", "user"]