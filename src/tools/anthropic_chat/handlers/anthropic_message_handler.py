import json
from typing import Generator, Any

from anthropic import Anthropic

from src.tools.local_mcp_tools.local_mcp_tool_base import OAToolBase
from src.tools.local_mcp_tools.local_mcp_tool_definitions import TOOL_DEFINITIONS
from src.data.valid_models import VALID_ANT_MODELS


class AnthropicMessageHandler:
    """
    Handles communication with Anthropic's messages API.
    Supports both synchronous and streaming responses, with optional extended thinking.
    """

    def __init__(self, client: Anthropic):
        self.client = client
        self.model = "claude-sonnet-4-5-20250929"
        self.tool_base = OAToolBase()

    # =========================================================================
    # Synchronous Handler (existing)
    # =========================================================================

    def handle_message(
        self, 
        instructions: str, 
        message: str, 
        history: list = None,
        model: str = "claude-sonnet-4-5-20250929"
    ) -> str:
        """
        Send a message to Anthropic and return the assistant's response.
        
        Args:
            instructions: System prompt
            message: Current user message  
            history: Optional list of previous messages
            model: Anthropic model to use
            
        Returns:
            The assistant's response text
        """
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

    # =========================================================================
    # Streaming Handler
    # =========================================================================

    def handle_message_stream(
        self,
        instructions: str,
        message: str,
        history: list = None,
        model: str = "claude-sonnet-4-5-20250929",
        enable_thinking: bool = False,
        thinking_budget: int = 10000
    ) -> Generator[dict[str, Any], None, str]:
        """
        Stream a message response from Anthropic with optional extended thinking.
        
        Yields dict events:
            - {"type": "thinking_start"} - Thinking block starting
            - {"type": "thinking", "text": "..."} - Thinking content chunk
            - {"type": "thinking_end"} - Thinking block complete
            - {"type": "content_start"} - Response content starting
            - {"type": "content", "text": "..."} - Text content chunk
            - {"type": "content_end"} - Response content complete
            - {"type": "tool_start", "name": "..."} - Tool execution starting
            - {"type": "tool_end", "name": "...", "result": "..."} - Tool complete
            - {"type": "error", "message": "..."} - Error occurred
            - {"type": "done", "full_response": "...", "full_thinking": "..."} - Complete
        
        Args:
            instructions: System prompt
            message: Current user message
            history: Optional list of previous messages
            model: Anthropic model to use
            enable_thinking: Whether to enable extended thinking
            thinking_budget: Token budget for thinking (if enabled)
            
        Returns:
            The complete response text (after generator exhausted)
        """
        if history is None:
            history = []

        if model not in VALID_ANT_MODELS:
            yield {"type": "error", "message": f"Invalid model: {model}"}
            return ""

        self.change_model(model)

        messages = list(history)
        messages.append({"role": "user", "content": message})

        full_response = ""
        full_thinking = ""

        try:
            full_response, full_thinking = yield from self._stream_with_tools(
                instructions=instructions,
                messages=messages,
                enable_thinking=enable_thinking,
                thinking_budget=thinking_budget
            )
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return ""

        yield {
            "type": "done", 
            "full_response": full_response,
            "full_thinking": full_thinking
        }
        return full_response

    def _stream_with_tools(
        self,
        instructions: str,
        messages: list,
        enable_thinking: bool = False,
        thinking_budget: int = 10000
    ) -> Generator[dict[str, Any], None, tuple[str, str]]:
        """
        Internal method to handle streaming with potential tool calls.
        
        Returns tuple of (full_response, full_thinking).
        """
        full_response = ""
        full_thinking = ""
        max_tool_rounds = 10
        tool_round = 0

        while tool_round < max_tool_rounds:
            tool_round += 1

            # Build API parameters
            params = {
                "model": self.model,
                "max_tokens": 8192,
                "system": instructions,
                "messages": messages,
                "tools": self._convert_tools_to_ant_format(TOOL_DEFINITIONS),
            }

            # Add extended thinking if enabled
            if enable_thinking:
                params["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
                params["max_tokens"] = 16000  # Need more for thinking

            # Track current block type and tool uses
            current_block_type = None
            tool_uses = []  # List of {id, name, input}
            current_tool_input = ""
            current_tool_id = None
            current_tool_name = None
            content_buffer = ""
            thinking_buffer = ""

            with self.client.messages.stream(**params) as stream:
                for event in stream:
                    event_type = event.type

                    # Block started
                    if event_type == "content_block_start":
                        block = event.content_block
                        current_block_type = block.type

                        if block.type == "thinking":
                            yield {"type": "thinking_start"}
                        elif block.type == "text":
                            yield {"type": "content_start"}
                        elif block.type == "tool_use":
                            current_tool_id = block.id
                            current_tool_name = block.name
                            current_tool_input = ""
                            yield {"type": "tool_start", "name": block.name}

                    # Block delta (content chunk)
                    elif event_type == "content_block_delta":
                        delta = event.delta

                        if hasattr(delta, "thinking"):
                            thinking_buffer += delta.thinking
                            full_thinking += delta.thinking
                            yield {"type": "thinking", "text": delta.thinking}

                        elif hasattr(delta, "text"):
                            content_buffer += delta.text
                            full_response += delta.text
                            yield {"type": "content", "text": delta.text}

                        elif hasattr(delta, "partial_json"):
                            # Tool input accumulating
                            current_tool_input += delta.partial_json

                    # Block ended
                    elif event_type == "content_block_stop":
                        if current_block_type == "thinking":
                            yield {"type": "thinking_end"}
                        elif current_block_type == "text":
                            yield {"type": "content_end"}
                        elif current_block_type == "tool_use":
                            # Parse and store the tool use
                            try:
                                tool_input = json.loads(current_tool_input) if current_tool_input else {}
                            except json.JSONDecodeError:
                                tool_input = {}

                            tool_uses.append({
                                "id": current_tool_id,
                                "name": current_tool_name,
                                "input": tool_input
                            })
                        
                        current_block_type = None

                    # Message complete
                    elif event_type == "message_stop":
                        pass  # Will check stop_reason after loop

                # Get the final message to check stop reason
                final_message = stream.get_final_message()
                stop_reason = final_message.stop_reason

            # Check if we need to handle tool calls
            if stop_reason == "tool_use" and tool_uses:
                # Build assistant message with all content blocks
                assistant_content = []
                
                if thinking_buffer:
                    assistant_content.append({
                        "type": "thinking",
                        "thinking": thinking_buffer
                    })
                
                if content_buffer:
                    assistant_content.append({
                        "type": "text",
                        "text": content_buffer
                    })
                
                for tool_use in tool_uses:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_use["id"],
                        "name": tool_use["name"],
                        "input": tool_use["input"]
                    })

                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Execute tools and build results
                tool_results = []
                for tool_use in tool_uses:
                    try:
                        result = self.tool_base.dispatch(tool_use["name"], **tool_use["input"])
                        result_str = json.dumps(result, default=str)
                    except Exception as e:
                        result_str = json.dumps({"error": str(e)})

                    yield {"type": "tool_end", "name": tool_use["name"], "result": result_str}

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": result_str
                    })

                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Reset buffers for next round
                thinking_buffer = ""
                content_buffer = ""
                
                # Continue loop to get follow-up response
                continue

            # No tool calls or finished normally - exit loop
            break

        return full_response, full_thinking

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _execute_tool_call(self, tool_use_block) -> str:
        """Execute a tool call and return the result as JSON string."""
        tool_name = tool_use_block.name
        tool_args = tool_use_block.input
        result = self.tool_base.dispatch(tool_name, **tool_args)
        return json.dumps(result, default=str)

    def _convert_tools_to_ant_format(self, openai_tools: list) -> list:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []
        for tool in openai_tools:
            if tool["type"] == "function":
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })
        return anthropic_tools

    def change_model(self, model: str):
        """Change the current model."""
        if model not in VALID_ANT_MODELS:
            raise ValueError(f"Invalid model: {model}. Must be one of {VALID_ANT_MODELS}")
        self.model = model
