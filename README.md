# Chunking Visualization

Visualize different chunking strategies on Markdown documents. Algorithms are based on the [LanceDB chunking analysis](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/).

This is the primary user-facing project documentation. Agent-oriented implementation notes are in `AGENT.MD`.

## Sources

- LanceDB: [Chunking analysis: which is the right chunking approach for your language?](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/)
- LanceDB: [Chunking techniques with LangChain and LlamaIndex](https://lancedb.com/blog/chunking-techniques-with-langchain-and-llamaindex/)

## Features

- **Upload .md** – Upload any Markdown file to chunk and visualize.
- **Load sample** – Load the bundled sample document from `data/sample.md`.
- **Algorithm selector** – Choose one of:
  1. **CharacterTextSplitter** – Fixed character count.
  2. **RecursiveCharacterTextSplitter** – Splits on paragraphs → lines → sentences → words.
  3. **TokenTextSplitter** – Approximate token-based splitting.
  4. **Semantic Chunking** – Sentence embeddings + similarity threshold.
  5. **Clustering (CRAG-style)** – Sentence embeddings + KMeans (contiguous output chunks).
  6. **LLM-based (Agent assisted)** – Paragraph-based proxy (real version would use an API).
  7. **HTML Header Splitter (LangChain)** – Splits HTML by header hierarchy.
  8. **Markdown Header Splitter (LangChain)** – Splits Markdown by `#` / `##` / `###`.
  9. **Code Splitter (LangChain)** – Code-aware recursive splitting.
  10. **Recursive JSON Splitter (LangChain)** – Splits nested JSON structures.
  11. **Markdown Node Parser (LlamaIndex)** – Parses Markdown into nodes.
  12. **HTML Node Parser (LlamaIndex)** – Parses HTML elements into nodes.
  13. **Sentence Splitter (LlamaIndex)** – Sentence-aware chunking with overlap.
  14. **Sentence Window Parser (LlamaIndex)** – Sentence chunks with windowed context.
  15. **Hierarchical Node Parser (LlamaIndex)** – Multi-level chunking (leaf nodes returned).

- **Per-algorithm params** – Chunk size, overlap, and limits where applicable.
- **Visual chunks** – Chunks listed as cards; click a chunk to highlight its region in the document.

## Setup

### Prerequisites

- Node.js `20.x` (see `.nvmrc`)
- Python `3.11.x` for backend (see `backend/.python-version`)
- `uv` installed: https://docs.astral.sh/uv/

**Frontend**

```bash
npm ci
npm run dev
```

Then open the URL shown (e.g. http://localhost:5173).

**Backend (Python chunking API)**

Chunking runs in Python as in the [LanceDB blog](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/). From the `backend/` directory:

```bash
cd backend
uv sync --frozen
```

Or with uv’s pip interface:

```bash
cd backend
uv pip install -r requirements.txt  # fallback path (not lockfile-based)
```

Then start the API:

```bash
uv run uvicorn app:app --reload --port 8000
```

The frontend expects the API at `http://localhost:8000` (override with `VITE_API_URL`).

## Build

```bash
npm run build
npm run preview
```

## Data

- Put your own `.md` files in `data/` and use **Upload .md** to open them, or use **Load sample** to use the bundled sample.

## Testing

From the `backend/` directory:

```bash
uv run python -m pytest tests/ -v              # fast tests only (~5s)
uv run python -m pytest tests/ -v --slow       # all tests including semantic & clustering (~40s)
```

The `--slow` flag enables tests that download the `paraphrase-multilingual-MiniLM-L12-v2` sentence-transformer model.

## Article coverage

Methods from both LanceDB articles are implemented in the backend and available in the UI selector.
