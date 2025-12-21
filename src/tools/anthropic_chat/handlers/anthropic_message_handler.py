import json
from anthropic import Anthropic

from src.tools.local_mcp_tools.local_mcp_tool_base import OAToolBase
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS
from src.data.valid_models import VALID_ANT_MODELS

class AnthropicMessageHandler:

    def __init__(self, client: Anthropic):
        self.client = client
        self.model = "claude-sonnet-4-5-20250929"
        self.tool_base = OAToolBase()

    def change_model(self, model: str):
        if model not in VALID_ANT_MODELS:
            raise ValueError(f"Invalid model: {model}. Must be one of {VALID_ANT_MODELS}")
        self.model = model

    def handle_message(self, instructions: str, message: str, history: list = None,
                       model: str = "claude-sonnet-4-5-20250929") -> str:
        if history is None:
            history = []

        self.change_model(model)

        messages = []
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=instructions,
            messages=messages,
            tools=self._convert_tools_to_ant_format(TOOL_DEFINITIONS)
        )

        while response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    result = self._execute_tool_call(content_block)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": result
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=instructions,
                messages=messages,
                tools=self._convert_tools_to_ant_format(TOOL_DEFINITIONS)
            )

        text_content = next(
            (block.text for block in response.content if hasattr(block, "text")),
            ""
        )
        return text_content

    def _execute_tool_call(self, tool_use_block) -> str:
        """Execute a tool call and return the result"""
        tool_name = tool_use_block.name
        tool_args = tool_use_block.input
        result = self.tool_base.dispatch(tool_name, **tool_args)
        return json.dumps(result, default=str)

    def _convert_tools_to_ant_format(self, openai_tools: list) -> list:
        """
        Convert OpenAI tool format to Anthropic format.

        """
        anthropic_tools = []
        for tool in openai_tools:
            if tool["type"] == "function":
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        return anthropic_tools
