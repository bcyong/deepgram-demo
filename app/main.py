from fastapi import FastAPI

from .routers import health, audit, transcribe, webhook

app = FastAPI()

app.include_router(health.router)
app.include_router(audit.router)
app.include_router(transcribe.router)
app.include_router(webhook.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
