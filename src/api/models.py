from fastapi import APIRouter
from src.tools.org_tools.get_models import get_models

router = APIRouter()

@router.get("/models")
async def get_all_models():
    data = get_models()
    return {"models": data}

