


class DataSummaryHelper:

    @staticmethod
    def generate_title(session_dict: dict, client, provider: str = "openai"):
        """Generate a concise 3-6 word title for a data session."""
        
        prompt = (
            f"You will be given a data session dict with tool name and parameters. "
            f"Generate a concise 3-6 word title for this data session.\n\n"
            f"{session_dict['messages']}\n\n"
            f"Make sure to include some type of unique identifier like the job number, or a specific detail about the session in the title to help differentiate sessions. "
            f"(i.e. 6489 PTOI OT Metrics, 6517 Eastlake Job Details, Jan Shop Hours, etc..)\n\n"
            f"Return ONLY the title, no quotes or extra text."
            f"Do NOT make up random titles or include irrelevant details."
        )

        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=30,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip().strip('"\'')[:75]

            elif provider == "anthropic":
                response = client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=30
                )
                return response.content[0].text.strip().strip('"\'')[:75]

        except Exception as e:
            print(f"[DataSummaryHelper] Title generation failed: {e}")
            return None


    @staticmethod
    def ai_data_session_summary(session_dict: dict, client, provider: str = "openai") -> str:
        """Generate a brief summary for the data session tooltip."""
        
        prompt = (
            f"You are a fabrication shop office assistant. You will be given a data session dict with tool info and sample data.\n"
            f"Generate a brief 1-4 sentence summary (15-124 words) describing what this data shows.\n"
            f"Focus on key metrics, time periods, or notable patterns.\n"
            f"\nPrefer concise and direct summaries over long padded explanations. Use the extra word count only when needed.\n\n"
            f"Session Dict:\n{session_dict}\n\n"
            f"Return ONLY the summary, no labels or extra text."
        )

        try:
            if provider == "openai":
                response = client.chat.completions.create(
                    model="gpt-5.2-chat-latest",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()

            elif provider == "anthropic":
                response = client.messages.create(
                    model="claude-opus-4-5-20251101",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400
                )
                return response.content[0].text.strip()

        except Exception as e:
            print(f"[DataSummaryHelper] Summary generation failed: {e}")
            return None

