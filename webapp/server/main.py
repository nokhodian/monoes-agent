from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .routers.health import router as health_router
from .routers.auth import router as auth_router
from .routers.actions import router as actions_router
from .routers.action_targets import router as action_targets_router
from .routers.people import router as people_router
from .routers.templates import router as templates_router
from .routers.social_lists import router as social_lists_router
from .routers.threads import router as threads_router
from .routers.configs import router as configs_router
from .errors import http_exception_handler, validation_exception_handler, generic_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS] if settings.CORS_ORIGINS != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(actions_router, prefix=settings.API_PREFIX)
app.include_router(action_targets_router, prefix=settings.API_PREFIX)
app.include_router(people_router, prefix=settings.API_PREFIX)
app.include_router(templates_router, prefix=settings.API_PREFIX)
app.include_router(social_lists_router, prefix=settings.API_PREFIX)
app.include_router(threads_router, prefix=settings.API_PREFIX)
app.include_router(configs_router, prefix=settings.API_PREFIX)
app.mount("/ui", StaticFiles(directory="webapp/ui", html=True), name="ui")

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
