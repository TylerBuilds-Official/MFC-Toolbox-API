import json
from typing import AsyncGenerator, Any

import openai

from src.tools.tool_utils import OAToolBase, get_chat_tools
from src.data.valid_models import VALID_OA_MODELS
from src.data.model_capabilities import get_capabilities


class OpenAIMessageHandler:
    """
    Handles communication with OpenAI's chat completions API.
    Supports both synchronous and streaming responses.
    """
    
    def __init__(self, client: openai.OpenAI):
        self.client = client
        self.model = "gpt-4o"
        self.tool_base = OAToolBase()

    def _get_token_param(self, value: int = 16384) -> dict:
        """
        Get the correct token limit parameter based on model.
        
        Newer models (gpt-4.1+, gpt-5+, o1, o3) use max_completion_tokens.
        Older models (gpt-3.5, gpt-4, gpt-4o) use max_tokens.
        """
        uses_completion_tokens = any(x in self.model for x in ["gpt-4.1", "gpt-5", "o1", "o3"])
        
        if uses_completion_tokens:
            return {"max_completion_tokens": value}
        else:
            return {"max_tokens": value}

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

        # Get filtered tools based on user role and specialties
        user_role = tool_context.get("user_role", "pending") if tool_context else "pending"
        user_specialties = tool_context.get("user_specialties", []) if tool_context else []
        filtered_tools = get_chat_tools(user_role, user_specialties)

        # Get model capabilities for token limits
        capabilities = get_capabilities(self.model)
        max_tokens = capabilities.default_max_tokens

        chat_params = {
            "model": self.model,
            "messages": messages,
            "tools": filtered_tools,
            **self._get_token_param(max_tokens),
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
                tools=filtered_tools,
                **self._get_token_param(max_tokens)
            )
            assistant_message = response.choices[0].message

        return assistant_message.content

    # =========================================================================
    # Async Streaming Handler
    # =========================================================================

    async def handle_message_stream(
        self, 
        instructions: str, 
        message: str, 
        history: list = None, 
        model: str = 'gpt-4o',
        tool_context: dict = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream a message response from OpenAI.
        
        This is an ASYNC generator - use `async for event in handler.handle_message_stream(...):`
        
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
            tool_context: Server-side context for tools
        """
        if history is None:
            history = []

        if model not in VALID_OA_MODELS:
            yield {"type": "error", "message": f"Invalid model: {model}"}
            return
            
        self.change_model(model)

        messages = [{"role": "system", "content": instructions}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        full_response = ""
        
        try:
            async for event in self._stream_with_tools(messages, tool_context=tool_context):
                if event.get("type") == "content":
                    full_response += event.get("text", "")
                yield event
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return
            
        yield {"type": "done", "full_response": full_response}

    async def _stream_with_tools(self, messages: list, tool_context: dict = None) -> AsyncGenerator[dict[str, Any], None]:
        """
        Internal async method to handle streaming with potential tool calls.
        Uses a loop to handle multiple rounds of tool calls.
        """
        max_tool_rounds = 10  # Safety limit
        tool_round = 0

        # Get filtered tools based on user role and specialties
        user_role = tool_context.get("user_role", "pending") if tool_context else "pending"
        user_specialties = tool_context.get("user_specialties", []) if tool_context else []
        filtered_tools = get_chat_tools(user_role, user_specialties)
        
        # Get model capabilities for token limits
        capabilities = get_capabilities(self.model)
        max_tokens = capabilities.default_max_tokens
        
        while tool_round < max_tool_rounds:
            tool_round += 1
            
            chat_params = {
                "model": self.model,
                "messages": messages,
                "tools": filtered_tools,
                "stream": True,
                **self._get_token_param(max_tokens),
            }
            
            if "gpt-5" in self.model:
                chat_params["temperature"] = 1
            else:
                chat_params["temperature"] = 0.7

            # Note: OpenAI's sync streaming is used here, but tool execution is async
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
                
                # Execute each tool call ASYNC
                for tc in tool_calls_buffer.values():
                    try:
                        tool_args = json.loads(tc["arguments"])
                    except Exception:
                        tool_args = {}
                    
                    yield {"type": "tool_start", "name": tc["name"]}
                    
                    try:
                        # Use async dispatch for proper event loop handling
                        result = await self.tool_base.dispatch_async(
                            tc["name"], 
                            context=tool_context, 
                            **tool_args
                        )
                        result_str = json.dumps(result, default=str)
                    except Exception as e:
                        result_str = json.dumps({"error": str(e)})
                    
                    yield {"type": "tool_end", "name": tc["name"], "params": tool_args, "result": result_str}
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result_str
                    })
                
                # Continue the loop to get the follow-up response
                continue
            
            # No tool calls or finished normally - exit loop
            break

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
