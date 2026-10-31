from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import users_collection
from app.deps import get_current_user
from app.schemas import Token, UserCreate, UserLogin, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


def to_user_out(user: dict) -> UserOut:
    return UserOut(id=str(user["_id"]), name=user["name"], email=user["email"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate):
    email = data.email.lower()

    if await users_collection.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = {
        "name": data.name,
        "email": email,
        "password": hash_password(data.password),
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(new_user)
    new_user["_id"] = result.inserted_id

    token = create_access_token(str(result.inserted_id))
    return Token(access_token=token, user=to_user_out(new_user))


@router.post("/login", response_model=Token)
async def login(data: UserLogin):
    user = await users_collection.find_one({"email": data.email.lower()})

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(str(user["_id"]))
    return Token(access_token=token, user=to_user_out(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user)):
    return to_user_out(current_user)