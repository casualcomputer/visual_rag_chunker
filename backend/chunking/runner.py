from .schemas import ChunkingParams, chunks_with_offsets
from .splitters import (
    character_split,
    recursive_split,
    token_split,
    semantic_split,
    clustering_split,
    llm_split,
)


def run_chunking(algorithm_id: str, text: str, params: ChunkingParams) -> list[dict]:
    if not text or not text.strip():
        return []

    dispatcher = {
        "character": character_split,
        "recursive": recursive_split,
        "token": token_split,
        "semantic": semantic_split,
        "clustering": clustering_split,
        "llm": llm_split,
    }
    fn = dispatcher.get(algorithm_id)
    if not fn:
        fn = recursive_split
    return fn(text, params)
