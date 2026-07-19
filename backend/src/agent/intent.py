"""
Router Node intent classification — Sprint 9.

Sprint 1-8 routed on keyword matching (backend/src/nlp.py). This
replaces that with the real LLM classifier docs/agent_design.md §3.1
specified from the start ("Intent Classification（LLM 分類）") —
keyword matching was always a placeholder for this.

`tool_choice` forces Claude to call `classify_intent`, so the result is
always one of the four valid categories — no free-text parsing, no
"model didn't follow instructions" failure mode to handle.
"""

INTENT_CLASSIFIER_TOOL = {
    "name": "classify_intent",
    "description": "Classify a bank customer service message into exactly one intent category.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": ["faq", "account", "card_loss", "handoff"],
                "description": (
                    "faq: general questions about bank products, services, rates, or rules that can be "
                    "answered from a knowledge base WITHOUT needing the user's own account data "
                    "(e.g. fees, loan terms, digital banking features, branch hours). "
                    "account: questions about the user's OWN account — balance, bill, transactions. "
                    "card_loss: user wants to report a lost/stolen card or block a card. "
                    "handoff: use ONLY when the user explicitly requests a human/live agent (e.g. '我要真人', "
                    "'speak to an agent') OR explicitly states they want to file a formal complaint "
                    "(e.g. '我要投訴', '我要申訴', 'I want to file a complaint'). "
                    "IMPORTANT — do NOT classify as handoff: messages that merely say a previous answer was "
                    "wrong, unhelpful, or not what they wanted (e.g. '你搞錯了，這不是我要的答案', "
                    "'that's not right', 'not helpful'). Those are just frustrated follow-ups on the SAME "
                    "topic — classify by what the underlying topic is (faq or account), not as handoff."
                ),
            }
        },
        "required": ["intent"],
    },
}

CLASSIFIER_SYSTEM_PROMPT = """\
You are an intent classifier for a bank customer service chatbot.
Read the user's message and call classify_intent with exactly one category.
Always call the tool — never respond with plain text.
You see only this one message, no prior conversation — if it's a short
reaction with no clear topic of its own (e.g. "that's wrong", "not
helpful"), classify it as faq rather than guessing account, card_loss,
or handoff."""


def classify_intent(client, model: str, message: str) -> str:
    result = client.messages.create(
        model=model,
        max_tokens=64,
        system=CLASSIFIER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": message}],
        tools=[INTENT_CLASSIFIER_TOOL],
        tool_choice={"type": "tool", "name": "classify_intent"},
    )
    for block in result.content:
        if block.type == "tool_use":
            return block.input["intent"]
    return "faq"  # unreachable while tool_choice forces the call; safe default if it ever isn't
