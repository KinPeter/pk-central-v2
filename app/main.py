import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.db import MongoDbManager
from app.common.logger import LoggingMiddleware, get_logger
from app.common.version import get_version

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_manager = MongoDbManager()
    db = await db_manager.connect()
    app.state.db = db

    app.state.logger = get_logger()

    yield

    await db_manager.close()


app = FastAPI(
    root_path=os.getenv("ROOT_PATH", ""),
    lifespan=lifespan,
    title="PK-Central API v2",
    version=get_version(),
    description="API for multiple PK-Central services",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://p-kin.com",
        "https://www.p-kin.com",
        "https://api.p-kin.com",
        "https://start.p-kin.com",
        "https://startv4.p-kin.com",
        "https://tripz.p-kin.com",
        "https://stuff.p-kin.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
