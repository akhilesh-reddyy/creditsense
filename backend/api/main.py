"""
CreditSense API — FastAPI application entrypoint.

Start with:
    uvicorn api.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from model.predictor import get_predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load model artefacts once at startup — not on first request
    print("Loading CreditSense model…")
    get_predictor()
    print("Model ready.")
    yield


app = FastAPI(
    title="CreditSense API",
    description=(
        "Explainable credit risk scoring engine. "
        "Returns default probability, risk band, SHAP-based top factors, "
        "and counterfactual recommendations per applicant."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "CreditSense", "docs": "/docs"}
