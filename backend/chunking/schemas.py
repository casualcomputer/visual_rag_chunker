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
        code_chunk_size: int = 800,
        code_chunk_overlap: int = 50,
        json_max_chunk_size: int = 400,
        llama_sentence_size: int = 1024,
        llama_sentence_overlap: int = 20,
        llama_sentence_window_size: int = 3,
        llama_hierarchical_large: int = 512,
        llama_hierarchical_medium: int = 256,
        llama_hierarchical_small: int = 128,
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
        self.code_chunk_size = code_chunk_size
        self.code_chunk_overlap = code_chunk_overlap
        self.json_max_chunk_size = json_max_chunk_size
        self.llama_sentence_size = llama_sentence_size
        self.llama_sentence_overlap = llama_sentence_overlap
        self.llama_sentence_window_size = llama_sentence_window_size
        self.llama_hierarchical_large = llama_hierarchical_large
        self.llama_hierarchical_medium = llama_hierarchical_medium
        self.llama_hierarchical_small = llama_hierarchical_small

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
            code_chunk_size=data.get("codeChunkSize", 800),
            code_chunk_overlap=data.get("codeChunkOverlap", 50),
            json_max_chunk_size=data.get("jsonMaxChunkSize", 400),
            llama_sentence_size=data.get("llamaSentenceSize", 1024),
            llama_sentence_overlap=data.get("llamaSentenceOverlap", 20),
            llama_sentence_window_size=data.get("llamaSentenceWindowSize", 3),
            llama_hierarchical_large=data.get("llamaHierarchicalLarge", 512),
            llama_hierarchical_medium=data.get("llamaHierarchicalMedium", 256),
            llama_hierarchical_small=data.get("llamaHierarchicalSmall", 128),
        )


def _find_normalized(text: str, chunk_text: str, search_from: int) -> tuple[int, int]:
    """Find chunk_text in text, tolerating whitespace normalization.

    Some splitters (e.g. MarkdownHeaderTextSplitter) transform the text:
    - ``\\n\\n`` becomes ``  \\n`` (markdown line-break)
    - leading/trailing whitespace may be added or removed

    This function walks through every non-empty line of chunk_text in order,
    finding each one sequentially in the original text.  This handles
    repeated lines (e.g. "Published: 17 May 2023" appearing multiple times
    in the same section).  Returns (start, end) offsets into the original
    text, or (-1, -1) if the first line is not found.
    """
    lines = [l.strip() for l in chunk_text.split("\n") if l.strip()]
    if not lines:
        return -1, -1

    first_pos = text.find(lines[0], search_from)
    if first_pos == -1:
        return -1, -1

    # Expand start to line boundary
    start = first_pos
    while start > 0 and text[start - 1] != "\n":
        start -= 1

    # Walk through all lines in order to find the correct last position.
    # This ensures repeated lines (like "Published: 17 May 2023") are
    # matched at their correct sequential occurrence.
    cursor = first_pos
    last_match_end = first_pos + len(lines[0])
    for line in lines[1:]:
        pos = text.find(line, cursor)
        if pos == -1:
            break
        cursor = pos + len(line)
        last_match_end = cursor

    end = last_match_end

    # Expand end past trailing whitespace up to the next non-blank line
    while end < len(text) and text[end] in " \t":
        end += 1
    # Consume trailing newlines (up to double-newline paragraph break)
    newlines = 0
    while end < len(text) and text[end] == "\n" and newlines < 2:
        end += 1
        newlines += 1

    return start, end


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

        if idx != -1:
            # Exact match found
            start = idx
            end = idx + len(chunk_text)
        else:
            # Whitespace-normalized match (e.g. MarkdownHeaderTextSplitter
            # converts \n\n to "  \n")
            start, end = _find_normalized(text, chunk_text, prev_end)
            if start == -1:
                start, end = _find_normalized(text, chunk_text, prev_start)
            if start == -1:
                # Last resort fallback
                start = prev_end
                end = prev_end + len(chunk_text)

        # Use the original text at the matched offsets so display preserves
        # the actual document formatting.
        display_text = text[start:end].strip() if end <= len(text) else chunk_text

        result.append({
            "index": i,
            "text": display_text,
            "startOffset": start,
            "endOffset": end,
        })
        prev_start = start
        prev_end = end
    return result
