from fastapi import FastAPI

import app.models

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok"}
