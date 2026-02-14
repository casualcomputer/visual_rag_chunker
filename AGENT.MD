# AGENT.MD

Agent-facing implementation notes for this repo.  
User-facing setup and product documentation lives in `README.md`.

## Scope

- Frontend visualizer: `src/`
- Python API and chunking logic: `backend/`

## Chunking methods (source of truth: backend dispatcher)

- `character` -> `CharacterTextSplitter`
- `recursive` -> `RecursiveCharacterTextSplitter`
- `token` -> `TokenTextSplitter`
- `semantic` -> sentence embeddings + similarity-threshold grouping
- `clustering` -> sentence embeddings + KMeans clustering (contiguous output)
- `llm` -> paragraph-based proxy for agent/LLM chunking
- `htmlHeader` -> LangChain `HTMLHeaderTextSplitter`
- `markdownHeader` -> LangChain `MarkdownHeaderTextSplitter` (`#`, `##`, `###`)
- `code` -> LangChain code-aware recursive splitter
- `recursiveJson` -> LangChain `RecursiveJsonSplitter`
- `llamaMarkdownNode` -> LlamaIndex `MarkdownNodeParser`
- `llamaHtmlNode` -> LlamaIndex `HTMLNodeParser`
- `llamaSentence` -> LlamaIndex `SentenceSplitter`
- `llamaSentenceWindow` -> LlamaIndex `SentenceWindowNodeParser`
- `llamaHierarchical` -> LlamaIndex `HierarchicalNodeParser` (leaf nodes)

See:
- `backend/chunking/runner.py`
- `backend/chunking/splitters.py`

## Key files

- API entrypoint: `backend/app.py`
- Request/response and params schema: `backend/chunking/schemas.py`
- Frontend chunking options/labels: `src/options.ts`
- Frontend chunking API calls: `src/chunking/`

## Local run commands

Frontend:

```bash
npm install
npm run dev
```

Backend:

```bash
cd backend
uv sync
uv run uvicorn app:app --reload --port 8000
```

Default API URL expected by frontend: `http://localhost:8000`.
