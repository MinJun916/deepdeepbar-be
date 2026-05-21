from fastapi import FastAPI

import app.models
from app.routers.auth_router import router as auth_router
from app.routers.menu_router import router as menu_router

app = FastAPI()

app.include_router(menu_router)
app.include_router(auth_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
