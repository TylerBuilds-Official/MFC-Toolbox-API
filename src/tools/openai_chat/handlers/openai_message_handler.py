import json
from typing import Generator, Any

import openai

from src.tools.local_mcp_tools.local_mcp_tool_base import OAToolBase
from src.tools.tool_registry import get_chat_tools
from src.data.valid_models import VALID_OA_MODELS


class OpenAIMessageHandler:
    """
    Handles communication with OpenAI's chat completions API.
    Supports both synchronous and streaming responses.
    """
    
    def __init__(self, client: openai.OpenAI):
        self.client = client
        self.model = "gpt-4o"
        self.tool_base = OAToolBase()

    # =========================================================================
    # Synchronous Handler (existing)
    # =========================================================================
    
    def handle_message(self, instructions: str, message: str, history: list = None, model: str = 'gpt-4o', tool_context: dict = None) -> str:
        """
        Send a message to OpenAI and return the assistant's response.
        
        Args:
            instructions: System prompt with guardrails and context
            message: Current user message
            history: Optional list of previous messages (for future full-history mode)
            model: OpenAI model to use (default: 'gpt-4o')
            tool_context: Server-side context for tools (user_id, conversation_id)
        
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

        # Get filtered tools based on user role
        user_role = tool_context.get("user_role", "pending") if tool_context else "pending"
        filtered_tools = get_chat_tools(user_role)

        chat_params = {
            "model": self.model,
            "messages": messages,
            "tools": filtered_tools,
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
                result = self._execute_tool_call(tool_call, context=tool_context)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=filtered_tools
            )
            assistant_message = response.choices[0].message

        return assistant_message.content

    # =========================================================================
    # Streaming Handler
    # =========================================================================

    def handle_message_stream(
        self, 
        instructions: str, 
        message: str, 
        history: list = None, 
        model: str = 'gpt-4o',
        tool_context: dict = None
    ) -> Generator[dict[str, Any], None, str]:
        """
        Stream a message response from OpenAI.
        
        Yields dict events:
            - {"type": "content", "text": "..."} - Text content chunk
            - {"type": "tool_start", "name": "..."} - Tool execution starting
            - {"type": "tool_end", "name": "...", "result": "..."} - Tool execution complete  
            - {"type": "error", "message": "..."} - Error occurred
            - {"type": "done", "full_response": "..."} - Stream complete
        
        Args:
            instructions: System prompt with guardrails and context
            message: Current user message
            history: Optional list of previous messages
            model: OpenAI model to use
            
        Returns:
            The complete response text (after generator exhausted)
        """
        if history is None:
            history = []

        if model not in VALID_OA_MODELS:
            yield {"type": "error", "message": f"Invalid model: {model}"}
            return ""
            
        self.change_model(model)

        messages = [{"role": "system", "content": instructions}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        full_response = ""
        
        try:
            full_response = yield from self._stream_with_tools(messages, tool_context=tool_context)
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return ""
            
        yield {"type": "done", "full_response": full_response}
        return full_response

    def _stream_with_tools(self, messages: list, tool_context: dict = None) -> Generator[dict[str, Any], None, str]:
        """
        Internal method to handle streaming with potential tool calls.
        Uses a loop to handle multiple rounds of tool calls.
        
        Returns the full accumulated response text.
        """
        full_response = ""
        max_tool_rounds = 10  # Safety limit
        tool_round = 0

        # Get filtered tools based on user role
        user_role = tool_context.get("user_role", "pending") if tool_context else "pending"
        filtered_tools = get_chat_tools(user_role)
        
        while tool_round < max_tool_rounds:
            tool_round += 1
            
            chat_params = {
                "model": self.model,
                "messages": messages,
                "tools": filtered_tools,
                "stream": True,
            }
            
            if "gpt-5" in self.model:
                chat_params["temperature"] = 1
            else:
                chat_params["temperature"] = 0.7

            stream = self.client.chat.completions.create(**chat_params)
            
            # Accumulators for this stream
            content_buffer = ""
            tool_calls_buffer = {}  # {index: {id, name, arguments}}
            finish_reason = None
            
            for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue
                    
                delta = choice.delta
                finish_reason = choice.finish_reason
                
                # Handle content delta
                if delta.content:
                    content_buffer += delta.content
                    full_response += delta.content
                    yield {"type": "content", "text": delta.content}
                
                # Handle tool call deltas (accumulate)
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        idx = tc_delta.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }
                        
                        if tc_delta.id:
                            tool_calls_buffer[idx]["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                tool_calls_buffer[idx]["name"] = tc_delta.function.name
                            if tc_delta.function.arguments:
                                tool_calls_buffer[idx]["arguments"] += tc_delta.function.arguments
            
            # Stream finished - check if we need to handle tool calls
            if finish_reason == "tool_calls" and tool_calls_buffer:
                # Build assistant message with tool calls for context
                assistant_msg = {
                    "role": "assistant",
                    "content": content_buffer if content_buffer else None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"]
                            }
                        }
                        for tc in tool_calls_buffer.values()
                    ]
                }
                messages.append(assistant_msg)
                
                # Execute each tool call
                for tc in tool_calls_buffer.values():
                    yield {"type": "tool_start", "name": tc["name"]}
                    
                    try:
                        tool_args = json.loads(tc["arguments"])
                        result = self.tool_base.dispatch(tc["name"], context=tool_context, **tool_args)
                        result_str = json.dumps(result, default=str)
                    except Exception as e:
                        result_str = json.dumps({"error": str(e)})
                    
                    yield {"type": "tool_end", "name": tc["name"], "result": result_str}
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str
                    })
                
                # Continue the loop to get the follow-up response
                continue
            
            # No tool calls or finished normally - exit loop
            break
        
        return full_response

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _execute_tool_call(self, tool_call, context: dict = None) -> str:
        """Execute a tool call and return the result as JSON string."""
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        result = self.tool_base.dispatch(tool_name, context=context, **tool_args)
        return json.dumps(result, default=str)

    def change_model(self, model: str):
        """Change the current model."""
        self.model = model
