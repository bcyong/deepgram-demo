from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
from .routers import health, audit, transcribe, webhook, keyterm, keyword

logger.info("Starting the application")

app = FastAPI()

app.include_router(health.router)
app.include_router(audit.router)
app.include_router(transcribe.router)
app.include_router(webhook.router)
app.include_router(keyterm.router)
app.include_router(keyword.router)


@app.get("/", response_class=HTMLResponse)
async def get():
    return HTMLResponse(
        content=open("app/templates/index.html").read(), media_type="text/html"
    )


@app.get("/audit", response_class=HTMLResponse)
async def get_audit():
    return HTMLResponse(
        content=open("app/templates/audit.html").read(), media_type="text/html"
    )
