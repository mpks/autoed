import secrets
import os
import yaml

from jose import JWTError, jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel

from typing import Annotated

router = APIRouter(prefix="/api/v1")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

if os.environ.get("AUTOED_CREDENTIALS"):
    with open(os.environ["AUTOED_CREDENTIALS"], "r") as fs:
        creds = yaml.safe_load(fs)
    AUTH_KEY = creds.get("auth_key") or secrets.token_hex(32)
else:
    AUTH_KEY = secrets.token_hex(32)


def get_creds() -> dict:
    if not os.environ.get("AUTOED_CREDENTIALS"):
        return {}
    try:
        with open(os.environ["AUTOED_CREDENTIALS"], "r") as fs:
            creds = yaml.safe_load(fs)
    except Exception:
        return {}
    return creds


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict):
    to_encode = data.copy()

    encoded_jwt = jwt.encode(to_encode, AUTH_KEY, algorithm="HS256")
    return encoded_jwt


async def validate_token(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        creds = get_creds()
        if not creds:
            raise JWTError
        decoded_data = jwt.decode(token, AUTH_KEY, algorithms=["HS256"])
        if decoded_data.get("username"):
            if not decoded_data["username"] == creds.get("username"):
                raise JWTError
        else:
            raise JWTError
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return None


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    creds = get_creds()
    if not creds:
        raise HTTPException(status_code=400, detail="Credentials file invalid")
    if not (
        form_data.username == creds.get("username")
        and form_data.password == creds.get("password")
    ):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"username": form_data.username},
    )
    return Token(access_token=access_token, token_type="bearer")
