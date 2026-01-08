from src.data.guardrails import BASE_GUARDRAILS, DEVELOPER_GUARDRAILS
from src.tools.auth import User
import time
from src.data.memory_management import MEMORY_POLICY

class Instructions:
    def __init__(self, state: dict, user: User = None, memories_text: str = None, project_instructions: str = None):
        self.state = state
        self.user = user
        self.memories_text = memories_text
        self.project_instructions = project_instructions
        self.memory_management = MEMORY_POLICY

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
            instructions.append("### USER MEMORIES")
            instructions.append(self.memories_text)
            instructions.append("")

        instructions.append("### MEMORY MANAGEMENT POLICY")
        instructions.append(self.memory_management)
        instructions.append("")

        instructions.append("### BASE USER INSTRUCTIONS")
        instructions.extend(BASE_GUARDRAILS)

        if self.state.get("is_developer"):
            instructions.append("### DEVELOPER INSTRUCTIONS")
            instructions.extend(DEVELOPER_GUARDRAILS)
            instructions.append("")

        # Role-based guardrails

        # Conversation context
        if self.state.get("conversation_summary"):
            instructions.append("\n### CONVERSATION CONTEXT")
            instructions.append("Summary of previous turns:")
            instructions.append(self.state["conversation_summary"])
            instructions.append("")
            instructions.append("### SUMMARY/CONTEXT INSTRUCTIONS:")
            instructions.append("Use get_conversation_messages() automatically before saying that you lack context.")
            instructions.append("Triggers: If the user asks, 'What did I/you just say?', requests repetition, references something not in your summary")
            instructions.append("Never tell the user you don't have context, unless you have exhausted all options to build context.")
            instructions.append("If you are uncertain, whether you have the full context to answer accurately, fetch conversation history to be sure.")
            instructions.append("")

        # Project-specific instructions (appended at end to give them priority)
        if self.project_instructions:
            instructions.append("\n### PROJECT INSTRUCTIONS")
            instructions.append("The following instructions apply to this conversation's project context:")
            instructions.append(self.project_instructions)

        return "\n".join(instructions)
