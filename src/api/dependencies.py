from fastapi import Request

def get_anthropic_message_handler(request: Request):
    return request.app.state.anthropic_message_handler

def get_openai_message_handler(request: Request):
    return request.app.state.openai_message_handler