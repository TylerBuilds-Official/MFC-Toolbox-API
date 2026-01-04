


class DataSummaryHelper:

    @staticmethod
    def generate_title(session_dict: dict, client, provider: str = "openai"):

        prompt = (f"You will be given a data session dict with all calls, and parameters. Generate a concise 3-6 word title for this data session."
                  f"\n\n{session_dict['messages']}"
                  f"\n\nMake sure to include some type of unique identifier in the title to help differentiate sessions. (i.e. 6489 PTOI OT Metrics, 6517 Eastlake Job Details, etc..)")

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
            print(f"[DataSummaryHelper] Title generation failed: {e}")


    @staticmethod
    def ai_data_session_summary(session_dict: dict, client, provider: str = "openai") -> str:
        prompt = (f"You are a fabrication shop office assistant. You will be given a data session dict, with all return values."
                  f"\nPlease generate a short and concise 5-20 word paragraph for the tooltip in the UI for this data session."
                  f"\n\nSession Dict: \n{session_dict}")

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
            print(f"[DataSummaryHelper] Title generation failed: {e}")


