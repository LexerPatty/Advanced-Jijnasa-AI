from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import users_collection
from app.routes import auth

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce unique emails at the database level
    await users_collection.create_index("email", unique=True)
    yield


app = FastAPI(title="Auth API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Auth API is running"}



