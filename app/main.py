from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.session import Base, engine
from app.api.v1.routes import router as api_router
import os

settings = get_settings()

# Ensure storage directories exist
for d in [
    settings.STORAGE_ROOT,
    settings.STORAGE_INPUT,
    settings.STORAGE_OUTPUT,
    settings.STORAGE_ARCHIVES,
]:
    os.makedirs(d, exist_ok=True)

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
