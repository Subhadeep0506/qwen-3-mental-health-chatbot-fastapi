from dotenv import load_dotenv

load_dotenv(".env")

import os
from contextlib import asynccontextmanager

import logfire
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from routes import auth, cases, chat, history, patient, user
from utils.state import State

state = State()
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    state.logger.info("Starting up...")
    yield
    state.logger.info("Shutting down...")


app = FastAPI(
    title="Qwen-2.5-VL API",
    description="API for Qwen-2.5-VL model with image and text inputs",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_headers=["*"],
)

logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    service_name="qwen-2.5-vl-api",
    service_version="0.0.1",
    environment=os.getenv("ENVIRONMENT", "development"),
)
logfire.instrument_fastapi(app, capture_headers=True)
logfire.instrument_sqlalchemy(engine)
logfire.instrument_httpx()
logfire.instrument_requests()
logfire.instrument_system_metrics(base="full")

app.include_router(chat.router, prefix="/api/v1/chat")
app.include_router(cases.router, prefix="/api/v1/cases")
app.include_router(history.router, prefix="/api/v1/history")
app.include_router(patient.router, prefix="/api/v1/patient")
app.include_router(user.router, prefix="/api/v1/users")
app.include_router(auth.router, prefix="/api/v1/auth")


@app.get("/")
async def root():
    return {"message": "Welcome to the Qwen-2.5-VL API"}
