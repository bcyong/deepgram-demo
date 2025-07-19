from fastapi import FastAPI
from loguru import logger
from .routers import health, audit, transcribe, webhook, keyterm

logger.info("Starting the application")

app = FastAPI()

app.include_router(health.router)
app.include_router(audit.router)
app.include_router(transcribe.router)
app.include_router(webhook.router)
app.include_router(keyterm.router)
