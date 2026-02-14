from .schemas import ChunkingParams, chunks_with_offsets
from .splitters import (
    character_split,
    recursive_split,
    token_split,
    semantic_split,
    clustering_split,
    llm_split,
    html_header_split,
    markdown_header_split,
    code_split,
    recursive_json_split,
    llama_markdown_node_split,
    llama_html_node_split,
    llama_sentence_split,
    llama_sentence_window_split,
    llama_hierarchical_split,
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
        "htmlHeader": html_header_split,
        "markdownHeader": markdown_header_split,
        "code": code_split,
        "recursiveJson": recursive_json_split,
        "llamaMarkdownNode": llama_markdown_node_split,
        "llamaHtmlNode": llama_html_node_split,
        "llamaSentence": llama_sentence_split,
        "llamaSentenceWindow": llama_sentence_window_split,
        "llamaHierarchical": llama_hierarchical_split,
    }
    fn = dispatcher.get(algorithm_id)
    if not fn:
        fn = recursive_split
    return fn(text, params)
