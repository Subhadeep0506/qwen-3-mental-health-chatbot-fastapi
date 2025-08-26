from dotenv import load_dotenv

load_dotenv(".env")

from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.database import Base, engine
from routes import cases, chat, history, patient
from utils.state import State
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import (
    RequestsInstrumentor,
)  # If using requests library
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

state = State()
Base.metadata.create_all(bind=engine)
resource = Resource(
    attributes={
        "service.name": "the-app"  # Important for identifying your service in traces
    }
)
otlp_exporter_grpc = OTLPSpanExporter(
    endpoint="otel-collector:4317",  # Collector's gRPC endpoint
    insecure=True,  # Use insecure connection in this example
)

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

span_processor_grpc = BatchSpanProcessor(otlp_exporter_grpc)
trace.get_tracer_provider().add_span_processor(span_processor_grpc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    # --- Expose metrics on startup ---
    # Ensure the instrumentator is available here or passed appropriately if needed,
    # but since it's defined globally below, it should be accessible.
    instrumentator.expose(app)
    logger.info("Startup complete. Metrics exposed.")  # Optional print statement
    yield
    # --- Code here would run on shutdown ---
    logger.info("Shutdown complete.")


app = FastAPI(
    title="Qwen-2.5-VL API",
    description="API for Qwen-2.5-VL model with image and text inputs",
    version="0.0.1",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator().instrument(app)

# Note: expose(app) is now called within the lifespan manager above

FastAPIInstrumentor.instrument_app(app)

app.include_router(chat.router, prefix="/chat")
app.include_router(cases.router, prefix="/cases")
app.include_router(history.router, prefix="/history")
app.include_router(patient.router, prefix="/patient")


@app.get("/")
async def root():
    return {"message": "Welcome to the Qwen-2.5-VL API"}
