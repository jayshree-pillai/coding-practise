def build_context(system_message, history, current_question, token_budget):
    """
    Build an LLM message list while staying within token_budget.
    history is a list of conversation turns:
    [
        {"user": "question1", "assistant": "answer1"},
        {"user": "question2", "assistant": "answer2"},
    ]
    Assume 1 word = 1 token for this exercise.
    """
    
    selected_turns = []

    messages = [
        {"role": "system", "content": system_message}
    ]
    used_tokens = len(system_message.split()) +  len(current_question.split()) 
    token_budget = token_budget-used_tokens

    for turn in reversed(history):
        user_tokens = len(turn["user"].split())
        assistant_tokens = len(turn["assistant"].split())

        if  user_tokens + assistant_tokens <= token_budget:
            selected_turns.append(turn)
            token_budget -= user_tokens + assistant_tokens
        else:
            break

    for turn in reversed(selected_turns):
        messages.append(
            {"role": "user", "content": turn["user"]}
        )
        messages.append(
            {"role": "assistant", "content": turn["assistant"]}
        )

    messages.append(
        {"role": "user", "content": current_question}
    )

    return messages