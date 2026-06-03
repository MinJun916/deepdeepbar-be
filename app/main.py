from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.core.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.middlewares.logging_middleware import LoggingMiddleware
from app.routers.admin_user_router import router as admin_user_router
from app.routers.auth_router import router as auth_router
from app.routers.menu_router import router as menu_router
from app.routers.recipe_router import router as recipe_router

tags_metadata = [
    {
        "name": "menus",
        "description": "손님용 메뉴 조회 및 관리자 메뉴 관리 API",
    },
    {
        "name": "recipes",
        "description": "직원용 레시피 조회 및 관리 API",
    },
    {
        "name": "auth",
        "description": "로그인, 토큰 재발급, 내 정보 조회 API",
    },
    {
        "name": "admin-users",
        "description": "관리자 전용 직원 계정 관리 API",
    },
]

app = FastAPI(
    title="DeepDeepBar API",
    description="""
    혼자와도 함께하는 밤이 깊어질수록 더 좋아지는 공간, 딥딥의 백엔드 API입니다.
    API 문서: https://deepdeep-api.gomoving.shop/docs
    API 코드: https://github.com/MinJun916/deepdeepbar-be
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "none",
        "displayRequestDuration": True,
        "filter": True,
    },
)

allowed_origins = [
    "http://localhost:3000",
    "https://deepdeepbar.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(menu_router)
app.include_router(auth_router)
app.include_router(recipe_router)
app.include_router(admin_user_router)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(LoggingMiddleware)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
