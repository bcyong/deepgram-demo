from fastapi import FastAPI

from .routers import health, audit

app = FastAPI()

app.include_router(health.router)
app.include_router(audit.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
