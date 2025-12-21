import json

import openai

from src.tools.local_mcp_tools.local_mcp_tool_base import OAToolBase
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS
from src.data.valid_models import VALID_OA_MODELS

class OpenAIMessageHandler:
    """
    Handles communication with OpenAI's chat completions API.
    """
    
    def __init__(self, client: openai.OpenAI):
        self.client = client
        self.model = "gpt-4o"
        self.tool_base = OAToolBase()

    def handle_message(self, instructions: str, message: str, history: list = None, model: str='gpt-4o') -> str:
        """
        Send a message to OpenAI and return the assistant's response.
        
        Args:
            instructions: System prompt with guardrails and context
            message: Current user message
            history: Optional list of previous messages (for future full-history mode)
            model: OpenAI model to use (default: 'gpt-4o')
        
        Returns:
            The assistant's response text
        """
        if history is None:
            history = []

        if model not in VALID_OA_MODELS:
            raise ValueError(f"Invalid model: {model}. Must be one of {VALID_OA_MODELS}")
        self.change_model(model)

        messages = [{"role": "system", "content": instructions}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        chat_params = {
            "model": self.model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
        }

        if "gpt-5" in self.model:
            chat_params["temperature"] = 1
        else:
            chat_params["temperature"] = 0.7

        response = self.client.chat.completions.create(**chat_params)

        assistant_message = response.choices[0].message

        while assistant_message.tool_calls:
            messages.append(assistant_message)

            for tool_call in assistant_message.tool_calls:
                result = self._execute_tool_call(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS
            )
            assistant_message = response.choices[0].message

        return assistant_message.content


    def _execute_tool_call(self, tool_call) -> str:
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        result = self.tool_base.dispatch(tool_name, **tool_args)

        return json.dumps(result, default=str)

    def change_model(self, model: str):
        self.model = model
