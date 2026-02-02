import os

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.lifespan import lifespan




def build_app():

    app = FastAPI(
        title="MFC Toolbox API",
        description="Multi-user chat interface for Metals Fabrication Company",
        version="0.3.0",
        lifespan=lifespan,
        swagger_ui_oauth2_redirect_url="/oauth2-redirect",
        swagger_ui_init_oauth={
            "usePkceWithAuthorizationCodeGrant": True,
            "clientId": os.getenv("AZURE_CLIENT_ID"),
        },
    )
    add_middleware(app)
    add_http_exception_handlers(app)
    add_global_exception_handler(app)

    return app


def add_middleware(app: FastAPI):

    # CORS middleware - allows WebUI to communicate with API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://localhost:5173",
            "https://10.0.59.72:5173",
            "https://10.0.0.10:6002",
            "https://10.0.0.12:6001",
            "https://10.0.0.12:6002",
            "https://fabcore.metalsfab.com"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def add_http_exception_handlers(app: FastAPI):

    # Middleware to log all requests and responses
    @app.middleware("http")
    async def log_requests(request, call_next):
        print(f"\n[REQUEST] {request.method} {request.url.path}")
        print(f"[REQUEST] Headers: {dict(request.headers)}")

        try:
            response = await call_next(request)
            print(f"[RESPONSE] Status: {response.status_code}")
            return response
        except Exception as e:
            print(f"[ERROR] Exception during request: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise


def add_global_exception_handler(app: FastAPI):

    # Exception handler for auth errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        print(f"[ERROR] Unhandled exception: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()

        # Return generic error
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )