from src.data.guardrails import BASE_GUARDRAILS, DEVELOPER_GUARDRAILS


class Instructions:
    def __init__(self, state: dict):
        self.state = state

    def build_instructions(self) -> str:
        instructions = []

        if self.state.get("is_developer"):
            instructions.extend(DEVELOPER_GUARDRAILS)

        instructions.extend(BASE_GUARDRAILS)


        if self.state.get("conversation_summary"):
            instructions.append("Conversation context (summary of previous turns):")
            instructions.append(self.state["conversation_summary"])

        return "\n".join(instructions)
