from fastapi import FastAPI

import app.models
from app.core.exceptions import AppError, app_error_handler
from app.routers.auth_router import router as auth_router
from app.routers.menu_router import router as menu_router
from app.routers.recipe_router import router as recipe_router

app = FastAPI()

app.include_router(menu_router)
app.include_router(auth_router)
app.include_router(recipe_router)

app.add_exception_handler(AppError, app_error_handler)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
