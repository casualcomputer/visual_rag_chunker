# Chunking Visualization

Visualize chunking strategies on a Markdown document (e.g. from the `data/` folder). Upload a .md file, select chunking algorithms from the [LanceDB chunking analysis](https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/), and see each chunk shown visually.

## Install & run

### Frontend

```bash
npm install
npm run dev
```

Open the URL shown (e.g. http://localhost:5173).

### Backend

```bash
cd backend
uv sync
uv run uvicorn app:app --reload --port 8000
```

Frontend expects the API at http://localhost:8000.
