import base64

from src.utils.file_utils._dataclasses.chat_file import ChatFile
from src.utils.file_utils.file_service import FileService
from src.utils.file_utils.extractors import extract_docx_as_markdown, extract_xlsx_as_text, compress_image_for_llm


def _is_docx(file: ChatFile) -> bool:
    return file.original_name.lower().endswith('.docx')


def build_user_content(message: str, files: list[ChatFile]) -> list[dict] | str:
    """Build multimodal content for Anthropic's messages API."""

    if not files:

        return message

    content_blocks: list[dict] = []

    for file in files:
        if file.category == "images":
            img_bytes, mime = compress_image_for_llm(file.storage_path)
            b64_data = base64.b64encode(img_bytes).decode('utf-8')
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime,
                    "data": b64_data,
                },
            })

        elif file.category == "documents" and _is_docx(file):
            # Docx — extract to markdown (not natively supported)
            text = extract_docx_as_markdown(file.storage_path)
            content_blocks.append({
                "type": "text",
                "text": f"[Document: {file.original_name}]\n\n{text}",
            })

        elif file.category == "documents":
            # PDF — native support
            b64_data = FileService.read_base64(file)
            content_blocks.append({
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": file.mime_type,
                    "data": b64_data,
                },
            })

        elif file.category == "spreadsheets":
            text = extract_xlsx_as_text(file.storage_path)
            content_blocks.append({
                "type": "text",
                "text": f"[Spreadsheet: {file.original_name}]\n\n{text}",
            })

        elif file.category == "text":
            text_content = FileService.read_text(file)
            content_blocks.append({
                "type": "text",
                "text": f"[File: {file.original_name}]\n{text_content}",
            })

    # User's message always comes last
    content_blocks.append({
        "type": "text",
        "text": message,
    })

    return content_blocks


def build_user_content_openai(message: str, files: list[ChatFile]) -> list[dict] | str:
    """Build multimodal content for OpenAI's chat completions API."""

    if not files:

        return message

    content_blocks: list[dict] = []

    for file in files:
        if file.category == "images":
            img_bytes, mime = compress_image_for_llm(file.storage_path)
            b64_data = base64.b64encode(img_bytes).decode('utf-8')
            data_uri = f"data:{mime};base64,{b64_data}"
            content_blocks.append({
                "type": "image_url",
                "image_url": {"url": data_uri},
            })

        elif file.category == "documents" and _is_docx(file):
            # Docx — extract to markdown for consistent handling
            text = extract_docx_as_markdown(file.storage_path)
            content_blocks.append({
                "type": "text",
                "text": f"[Document: {file.original_name}]\n\n{text}",
            })

        elif file.category == "documents":
            # PDF — native support
            b64_data = FileService.read_base64(file)
            data_uri = f"data:{file.mime_type};base64,{b64_data}"
            content_blocks.append({
                "type": "file",
                "file": {
                    "filename": file.original_name,
                    "file_data": data_uri,
                },
            })

        elif file.category == "spreadsheets":
            text = extract_xlsx_as_text(file.storage_path)
            content_blocks.append({
                "type": "text",
                "text": f"[Spreadsheet: {file.original_name}]\n\n{text}",
            })

        elif file.category == "text":
            text_content = FileService.read_text(file)
            content_blocks.append({
                "type": "text",
                "text": f"[File: {file.original_name}]\n{text_content}",
            })

    content_blocks.append({
        "type": "text",
        "text": message,
    })

    return content_blocks
