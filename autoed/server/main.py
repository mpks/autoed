import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from autoed.server.api import router
from autoed.server.auth import router as authrouter

app = FastAPI(title="Murfey instrument server", debug=True)

if os.environ.get("AUTOED_SERVER_ALLOWED_CLIENTS"):
    allow_origins = os.environ["AUTOED_SERVER_ALLOWED_CLIENTS"].split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router)
app.include_router(authrouter)
