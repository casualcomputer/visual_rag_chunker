"""
FastAPI backend for chunking visualization.
Chunking algorithms implemented as in the LanceDB blog.
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chunking import run_chunking
from chunking.schemas import ChunkingParams

# Ensure NLTK data is available
def _ensure_nltk():
    try:
        import nltk
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)


app = FastAPI(title="Chunking Visualization API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChunkRequest(BaseModel):
    text: str
    algorithm: str
    params: dict = {}


class ChunkResponse(BaseModel):
    chunks: list[dict]


@app.on_event("startup")
def startup():
    _ensure_nltk()


@app.post("/chunk", response_model=ChunkResponse)
def chunk_text(req: ChunkRequest):
    if not req.text or not req.text.strip():
        return ChunkResponse(chunks=[])
    params = ChunkingParams.from_request(req.params or {})
    try:
        chunks = run_chunking(req.algorithm, req.text, params)
        return ChunkResponse(chunks=chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
