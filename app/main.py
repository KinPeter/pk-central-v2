import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.config import get_allowed_origins
from app.common.db import MongoDbManager
from app.common.environment import load_environment
from app.common.logger import LoggingMiddleware, get_logger
from app.common.version import get_version
from app.modules.activities import activities
from app.modules.auth import auth
from app.modules.birthdays import birthdays
from app.modules.flights import flights
from app.modules.notes import notes
from app.modules.personal_data import personal_data
from app.modules.proxy import proxy
from app.modules.reddit import reddit
from app.modules.shortcuts import shortcuts
from app.modules.start_settings import start_settings
from app.modules.visits import visits

load_dotenv()

allow_origins = get_allowed_origins()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = get_logger()
    env = load_environment()

    db_manager = MongoDbManager(env, logger)
    db = await db_manager.connect()

    app.state.db = db
    app.state.env = env
    app.state.logger = logger

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
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth.router)
app.include_router(start_settings.router)
app.include_router(notes.router)
app.include_router(shortcuts.router)
app.include_router(personal_data.router)
app.include_router(activities.router)
app.include_router(birthdays.router)
app.include_router(flights.router)
app.include_router(visits.router)
app.include_router(proxy.router)
app.include_router(reddit.router)
