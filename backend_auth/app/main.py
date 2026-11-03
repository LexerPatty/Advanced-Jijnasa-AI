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




# if __name__ == "__main__":
#     import atexit
#     import subprocess
#     import time
#     import uvicorn

#     backend = subprocess.Popen(
#         [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
#         cwd=r"P:\Advanced-Jijnasa-AI\Backend",
#     )
#     atexit.register(backend.terminate)

#     time.sleep(3)
#     if backend.poll() is not None:
#         print(f"!!! Backend exited with code {backend.returncode}. Check the error above.")

#     uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

