"""
FastAPI backend for chunking visualization.
Chunking algorithms implemented as in the LanceDB blog.
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chunking import run_chunking
from chunking.schemas import ChunkingParams

# Keep NLTK assets in-project so setup is reproducible across machines.
NLTK_DATA_DIR = Path(__file__).resolve().parent / ".nltk_data"


def _ensure_nltk():
    import nltk

    nltk.data.path.insert(0, str(NLTK_DATA_DIR))
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        nltk.download("punkt_tab", download_dir=str(NLTK_DATA_DIR), quiet=True)
        nltk.data.find("tokenizers/punkt_tab")


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
