from fastapi import FastAPI
import logging
from .routers import health, audit, transcribe, webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting the application")

app = FastAPI()

app.include_router(health.router)
app.include_router(audit.router)
app.include_router(transcribe.router)
app.include_router(webhook.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
