# Chunking Visualization

Visualize different chunking strategies on Markdown documents. Algorithms are based on the [LanceDB chunking analysis](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/).

## Features

- **Upload .md** – Upload any Markdown file to chunk and visualize.
- **Load sample** – Load the bundled sample document from `data/sample.md`.
- **Algorithm selector** – Choose one of:
  1. **CharacterTextSplitter** – Fixed character count.
  2. **RecursiveCharacterTextSplitter** – Splits on paragraphs → lines → sentences → words.
  3. **TokenTextSplitter** – Approximate token-based splitting.
  4. **Semantic Chunking** – Sentence-boundary grouping (no embeddings in-browser).
  5. **Clustering (CRAG-style)** – Paragraph-based grouping.
  6. **LLM-based (Agent assisted)** – Paragraph-based proxy (real version would use an API).

- **Per-algorithm params** – Chunk size, overlap, and limits where applicable.
- **Visual chunks** – Chunks listed as cards; click a chunk to highlight its region in the document.

## Setup

**Frontend**

```bash
npm install
npm run dev
```

Then open the URL shown (e.g. http://localhost:5173).

**Backend (Python chunking API)**

Chunking runs in Python as in the [LanceDB blog](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/). From the `backend/` directory:

```bash
cd backend
uv sync
```

Or with uv’s pip interface:

```bash
cd backend
uv pip install -r requirements.txt
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
