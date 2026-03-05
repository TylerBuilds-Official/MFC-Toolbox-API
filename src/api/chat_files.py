from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response

from src.tools.auth import User, require_active_user
from src.utils.file_utils import FileService
from src.utils.file_utils.extractors import extract_docx_as_markdown, extract_xlsx_as_text


router = APIRouter()


@router.post("/chat/files/upload")
async def upload_chat_file(
        file: UploadFile = File(...),
        user: User = Depends(require_active_user) ):
    """Upload a file for use in a chat message."""

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    try:
        file_bytes = await file.read()

        chat_file = FileService.upload_file(
            user_id=user.id,
            filename=file.filename,
            mime_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes,
        )

        return chat_file.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/files/{file_id}")
async def get_chat_file_info(file_id: str, user: User = Depends(require_active_user)):
    """Get metadata for an uploaded file."""

    chat_file = FileService.get_file(file_id)

    if not chat_file:
        raise HTTPException(status_code=404, detail="File not found")

    if chat_file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return chat_file.to_dict()


@router.get("/chat/files/{file_id}/content")
async def get_chat_file_content(file_id: str, user: User = Depends(require_active_user)):
    """Serve raw file content with correct MIME type."""

    chat_file = FileService.get_file(file_id)

    if not chat_file:
        raise HTTPException(status_code=404, detail="File not found")

    if chat_file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    file_bytes = FileService._storage.read_file_bytes(chat_file.storage_path)

    return Response(
        content=file_bytes,
        media_type=chat_file.mime_type,
        headers={"Content-Disposition": f'inline; filename="{chat_file.original_name}"'},
    )


@router.get("/chat/files/{file_id}/text")
async def get_chat_file_text(file_id: str, user: User = Depends(require_active_user)):
    """Get text content of a file for modal display."""

    chat_file = FileService.get_file(file_id)

    if not chat_file:
        raise HTTPException(status_code=404, detail="File not found")

    if chat_file.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if chat_file.category == "text":
        text = FileService.read_text(chat_file)

        return {"content": text, "filename": chat_file.original_name, "format": "text"}

    elif chat_file.category == "documents":
        if chat_file.original_name.lower().endswith('.docx'):
            text = extract_docx_as_markdown(chat_file.storage_path)

            return {"content": text, "filename": chat_file.original_name, "format": "markdown"}

        return {"content_url": f"/chat/files/{file_id}/content", "filename": chat_file.original_name, "format": "pdf"}

    elif chat_file.category == "spreadsheets":
        text = extract_xlsx_as_text(chat_file.storage_path)

        return {"content": text, "filename": chat_file.original_name, "format": "spreadsheet"}

    raise HTTPException(status_code=400, detail="File type does not support text preview")
