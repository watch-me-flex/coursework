from fastapi.applications import FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import UserContextMiddleware
from app.config import settings
from app.routers.router import router
from app.db.database import DBSession

def create_app() -> FastAPI:
    app: FastAPI = FastAPI(
        title=settings.PROJECT_NAME,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(UserContextMiddleware)
    app.add_event_handler(event_type="startup", func=DBSession._init_db)
    app.include_router(router=router, prefix=settings.API_PREFIX + "/v1")
    return app
