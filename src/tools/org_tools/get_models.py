from src.data.valid_models import VALID_OA_MODELS as valid_oa_models
from src.data.valid_models import VALID_ANT_MODELS as valid_ant_models


def get_models():
    return {
        "openai_models": valid_oa_models,
        "claude_models": valid_ant_models
    }

