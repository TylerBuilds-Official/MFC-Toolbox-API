from dotenv import load_dotenv
load_dotenv()

from src.app import build_app

from src.api.auth import router as              auth_router
from src.api.health import router as            health_router
from src.api.models import router as            models_router
from src.api.settings import router as          settings_router
from src.api.user_info import router as         user_info_router
from src.api.data.utils import router as        data_utils_router
from src.api.data.sessions import router as     data_sessions_router
from src.api.data.groups import router as       data_groups_router
from src.api.admin import router as             admin_router
from src.api.conversations import router as             conversations_router
from src.api.conversation_projects import router as     conversation_projects_router
from src.api.tools import router as                     tools_router
from src.api.artifacts import router as         artifacts_router
from src.api.memories import router as          memories_router
from src.api.chat import router as              chat_router
from src.api.agent_ws import router as          agent_router
from src.api.connectors import router as        connectors_router


app = build_app()

app.include_router(auth_router, tags=["Auth"])
app.include_router(health_router, tags=["Health"])
app.include_router(models_router, tags=["Models"])
app.include_router(settings_router, tags=["Settings"])
app.include_router(connectors_router, tags=["Connectors"])
app.include_router(user_info_router, tags=["User Info"])
app.include_router(data_utils_router, tags=["Data Utils"])
app.include_router(data_sessions_router, tags=["Data Sessions"])
app.include_router(data_groups_router, tags=["Data Groups"])
app.include_router(admin_router, tags=["Admin"])
# IMPORTANT: conversation_projects must come BEFORE conversations
# so /conversations/projects routes match before /conversations/{id}
app.include_router(conversation_projects_router, tags=["Conversation Projects"])
app.include_router(conversations_router, tags=["Conversations"])
app.include_router(tools_router, tags=["Tools"])
app.include_router(artifacts_router, tags=["Artifacts"])
app.include_router(memories_router, tags=["Memories"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(agent_router, tags=["Agent"])
