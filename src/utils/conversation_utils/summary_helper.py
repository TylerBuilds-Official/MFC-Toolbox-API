

class ConversationSummaryHelper:

    @staticmethod
    def should_update_summary(message_count: int, interval: int = 3) -> bool:
        return message_count == 1 or message_count % interval == 0



    @staticmethod
    def format_messages_for_summary(messages):
        return '\n'.join(
            f"{m.role.capitalize()}: {m.content}"
            for m in messages)



    @staticmethod
    def get_last_message_preview(messages, max_length: int = 100) -> str:
        if not messages:
            return ""
        last_message = messages[-1]
        prefix = "You: " if last_message.role == "user" else ""
        content = last_message.content

        if len(content) > max_length:
            return f"{prefix}{content[:max_length]}..."
        return f"{prefix}{content}"



    @staticmethod
    def generate_title(first_message: str, client, provider: str = "openai") -> str:
        prompt = (
            "Generate a concise 3-6 word title for a conversation that starts with this message. "
            "Return ONLY the title, no quotes, no punctuation at the end.\n\n"
            f"Message: {first_message[:500]}"
        )

        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=20,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()[:50]

            elif provider == "anthropic":
                response = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=20
                )
                return response.content[0].text.strip()[:50]

        except Exception as e:
            print(f"[ConversationSummaryHelper] Title generation failed: {e}")

        # Fallback: truncate first message
        return first_message[:40] + "..." if len(first_message) > 40 else first_message



    @staticmethod
    def ai_summary(formatted_messages: str, client, provider: str = "openai") -> str:
        prompt = (
            "Summarize this conversation in 1-2 brief sentences. "
            "Focus on the main topic and outcome.\n\n"
            f"{formatted_messages}")

        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100,
                    temperature=0.5)
                return response.choices[0].message.content.strip()

            if provider == "anthropic":
                reponse = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=100)
                return reponse.content[0].text.strip()

        except Exception as e:
            print(f"[ConversationSummaryHelper] AI Summary Failed: {e}")
            lines = formatted_messages.strip().split('\n')
            if lines:
                last_line = lines[-1]
                return last_line[:150] + "..." if len(last_line) > 150 else last_line
            return ""



    @staticmethod
    def build_summary(messages, client, provider: str = "openai"):
        summary = ConversationSummaryHelper.format_messages_for_summary(messages)
        ai_summary = ConversationSummaryHelper.ai_summary(summary, client=client, provider=provider)
        return f"Summary:\n    {ai_summary}"





