from anthropic import Anthropic


class AnthropicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Anthropic(api_key=self.api_key)