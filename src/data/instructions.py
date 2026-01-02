from src.data.guardrails import BASE_GUARDRAILS, DEVELOPER_GUARDRAILS
from src.tools.auth import User
import time


class Instructions:
    def __init__(self, state: dict, user: User = None, memories_text: str = None):
        self.state = state
        self.user = user
        self.memories_text = memories_text

    def build_instructions(self) -> str:
        instructions = []
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # User identity block
        if self.user:
            instructions.append("### CURRENT USER")
            instructions.append(f"You are speaking with {self.user.display_name}.")
            instructions.append(f"Email: {self.user.email}")
            instructions.append(f"System Role: {self.user.role}")
            instructions.append(f"Current Time: {current_time}")
            instructions.append("")

        # User memories block
        if self.memories_text:
            instructions.append(self.memories_text)

        # Role-based guardrails
        if self.state.get("is_developer"):
            instructions.extend(DEVELOPER_GUARDRAILS)

        instructions.extend(BASE_GUARDRAILS)

        # Conversation context
        if self.state.get("conversation_summary"):
            instructions.append("\n### CONVERSATION CONTEXT")
            instructions.append("Summary of previous turns:")
            instructions.append(self.state["conversation_summary"])

        return "\n".join(instructions)
