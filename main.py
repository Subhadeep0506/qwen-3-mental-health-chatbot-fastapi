from dotenv import load_dotenv

load_dotenv(".env")


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import Base, engine
from routes import cases, chat, history, patient
from utils.state import State

state = State()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Qwen-2.5-VL API",
    description="API for Qwen-2.5-VL model with image and text inputs",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router, prefix="/chat")
app.include_router(cases.router, prefix="/cases")
app.include_router(history.router, prefix="/history")
app.include_router(patient.router, prefix="/patient")


@app.get("/")
async def root():
    return {"message": "Welcome to the Qwen-2.5-VL API"}
