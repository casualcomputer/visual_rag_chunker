"""
FastAPI backend for chunking visualization.
Chunking algorithms implemented as in the LanceDB blog.
"""
from pathlib import Path
import re

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
    warning: str | None = None


HTML_ONLY_FALLBACKS = {
    "htmlHeader": "markdownHeader",
    "llamaHtmlNode": "llamaMarkdownNode",
}


def _looks_like_html(text: str) -> bool:
    # A simple, robust check for actual HTML tags.
    return bool(re.search(r"<\s*/?\s*[a-zA-Z][a-zA-Z0-9:-]*\b[^>]*>", text))


@app.on_event("startup")
def startup():
    _ensure_nltk()


@app.post("/chunk", response_model=ChunkResponse)
def chunk_text(req: ChunkRequest):
    if not req.text or not req.text.strip():
        return ChunkResponse(chunks=[])
    params = ChunkingParams.from_request(req.params or {})
    try:
        algorithm = req.algorithm
        warning: str | None = None

        fallback_algorithm = HTML_ONLY_FALLBACKS.get(algorithm)
        if fallback_algorithm and not _looks_like_html(req.text):
            warning = (
                f"Selected algorithm '{algorithm}' expects HTML input. "
                f"Applied fallback '{fallback_algorithm}' for this document."
            )
            algorithm = fallback_algorithm

        chunks = run_chunking(algorithm, req.text, params)
        return ChunkResponse(chunks=chunks, warning=warning)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
