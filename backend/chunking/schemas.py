from typing import Any, Optional, TypedDict


class Chunk(TypedDict):
    index: int
    text: str
    startOffset: int
    endOffset: int


class ChunkingParams:
    """Parameters for chunking algorithms (matches frontend)."""

    def __init__(
        self,
        character_size: int = 500,
        character_overlap: int = 50,
        recursive_size: int = 500,
        recursive_overlap: int = 50,
        token_size: int = 256,
        token_overlap: int = 25,
        semantic_max: int = 800,
        semantic_min: int = 100,
        semantic_percentile: int = 90,
        clustering_max: int = 1200,
        clustering_min: int = 100,
        num_clusters: Optional[int] = None,
        llm_max: int = 600,
        **kwargs: Any,
    ):
        self.character_size = character_size
        self.character_overlap = character_overlap
        self.recursive_size = recursive_size
        self.recursive_overlap = recursive_overlap
        self.token_size = token_size
        self.token_overlap = token_overlap
        self.semantic_max = semantic_max
        self.semantic_min = semantic_min
        self.semantic_percentile = semantic_percentile
        self.clustering_max = clustering_max
        self.clustering_min = clustering_min
        self.num_clusters = num_clusters
        self.llm_max = llm_max

    @classmethod
    def from_request(cls, data: dict) -> "ChunkingParams":
        return cls(
            character_size=data.get("characterSize", 500),
            character_overlap=data.get("characterOverlap", 50),
            recursive_size=data.get("recursiveSize", 500),
            recursive_overlap=data.get("recursiveOverlap", 50),
            token_size=data.get("tokenSize", 256),
            token_overlap=data.get("tokenOverlap", 25),
            semantic_max=data.get("semanticMax", 800),
            semantic_min=data.get("semanticMin", 100),
            semantic_percentile=data.get("semanticPercentile", 90),
            clustering_max=data.get("clusteringMax", 1200),
            clustering_min=data.get("clusteringMin", 100),
            num_clusters=data.get("numClusters"),
            llm_max=data.get("llmMax", 600),
        )


def chunks_with_offsets(text: str, chunk_texts: list[str]) -> list[dict]:
    """Compute startOffset/endOffset for each chunk by finding it in the original text."""
    result = []
    prev_start = 0
    prev_end = 0
    for i, chunk_text in enumerate(chunk_texts):
        if not chunk_text:
            result.append({"index": i, "text": "", "startOffset": prev_end, "endOffset": prev_end})
            continue

        # Allow backtracking for overlap-based splitters where the next chunk can start
        # before the previous chunk's end.
        search_start = max(0, prev_end - len(chunk_text))
        idx = text.find(chunk_text, search_start)
        if idx == -1:
            idx = text.find(chunk_text, prev_start)
        if idx == -1:
            # Fallback: treat as contiguous (e.g. normalized whitespace)
            idx = prev_end
        result.append({
            "index": i,
            "text": chunk_text,
            "startOffset": idx,
            "endOffset": idx + len(chunk_text),
        })
        prev_start = idx
        prev_end = idx + len(chunk_text)
    return result
