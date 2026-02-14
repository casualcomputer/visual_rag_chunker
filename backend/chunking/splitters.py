"""
Chunking algorithms as in the LanceDB blog:
https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/
and:
https://lancedb.com/blog/chunking-techniques-with-langchain-and-llamaindex/
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from langchain_text_splitters import (
    CharacterTextSplitter,
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
    RecursiveJsonSplitter,
)
from langchain_text_splitters import TokenTextSplitter  # uses tiktoken
from langchain_text_splitters.base import Language

from .schemas import ChunkingParams, chunks_with_offsets

if TYPE_CHECKING:
    pass


def character_split(text: str, params: ChunkingParams) -> list[dict]:
    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=params.character_size,
        chunk_overlap=params.character_overlap,
    )
    chunks = splitter.split_text(text)
    return chunks_with_offsets(text, chunks)


def recursive_split(text: str, params: ChunkingParams) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=params.recursive_size,
        chunk_overlap=params.recursive_overlap,
    )
    chunks = splitter.split_text(text)
    return chunks_with_offsets(text, chunks)


def token_split(text: str, params: ChunkingParams) -> list[dict]:
    splitter = TokenTextSplitter(
        chunk_size=params.token_size,
        chunk_overlap=params.token_overlap,
    )
    chunks = splitter.split_text(text)
    return chunks_with_offsets(text, chunks)


def semantic_split(text: str, params: ChunkingParams) -> list[dict]:
    """Sequential semantic chunking: NLTK sentences + cosine similarity threshold (blog)."""
    import re
    import numpy as np
    from nltk.tokenize import PunktSentenceTokenizer, sent_tokenize
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    sentence_spans: list[tuple[int, int]] = []
    try:
        sentence_spans = list(PunktSentenceTokenizer().span_tokenize(text))
    except Exception:
        sentence_spans = []
    try:
        sentences = sent_tokenize(text)
    except Exception:
        sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s for s in sentences if s.strip()]
    if not sentence_spans and sentences:
        cursor = 0
        for sentence in sentences:
            idx = text.find(sentence, cursor)
            if idx == -1:
                idx = text.find(sentence)
            if idx == -1:
                continue
            sentence_spans.append((idx, idx + len(sentence)))
            cursor = idx + len(sentence)
    if not sentence_spans:
        return chunks_with_offsets(text, [text] if text.strip() else [])
    if len(sentence_spans) != len(sentences):
        limit = min(len(sentence_spans), len(sentences))
        sentence_spans = sentence_spans[:limit]
        sentences = sentences[:limit]

    # Build chunks with combined context (prev + curr + next) for embedding, as in blog
    chunk_dicts = [{"chunk": s} for s in sentences]
    for i in range(len(chunk_dicts)):
        combined = ""
        if i > 0:
            combined += chunk_dicts[i - 1]["chunk"]
        combined += chunk_dicts[i]["chunk"]
        if i < len(chunk_dicts) - 1:
            combined += chunk_dicts[i + 1]["chunk"]
        chunk_dicts[i]["combined_chunk"] = combined

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    combined_texts = [d["combined_chunk"] for d in chunk_dicts]
    embeddings = model.encode(combined_texts, show_progress_bar=False)
    for i, d in enumerate(chunk_dicts):
        d["embedding"] = embeddings[i]

    distances = []
    for i in range(len(chunk_dicts) - 1):
        sim = cosine_similarity([chunk_dicts[i]["embedding"]], [chunk_dicts[i + 1]["embedding"]])[0][0]
        dist = 1 - sim
        distances.append(dist)
        chunk_dicts[i]["distance_to_next"] = dist

    if not distances:
        return chunks_with_offsets(text, [text] if text.strip() else [])

    threshold = float(np.percentile(distances, params.semantic_percentile))
    break_indices = [0]
    for i, d in enumerate(chunk_dicts[:-1]):
        if d["distance_to_next"] >= threshold:
            break_indices.append(i + 1)
    break_indices.append(len(chunk_dicts))

    raw_chunks: list[list[int]] = []
    for j in range(len(break_indices) - 1):
        start, end = break_indices[j], break_indices[j + 1]
        raw_chunks.append(list(range(start, end)))

    max_chars = max(params.semantic_min, params.semantic_max)
    min_chars = min(params.semantic_min, max_chars)

    # Enforce max chunk size by splitting on sentence boundaries.
    max_limited: list[list[int]] = []
    for sentence_group in raw_chunks:
        current_group: list[int] = []
        current_len = 0
        for sentence_idx in sentence_group:
            sentence = chunk_dicts[sentence_idx]["chunk"]
            extra = len(sentence) if not current_group else len(sentence) + 1
            if current_group and current_len + extra > max_chars:
                max_limited.append(current_group)
                current_group = [sentence_idx]
                current_len = len(sentence)
            else:
                current_group.append(sentence_idx)
                current_len += extra
        if current_group:
            max_limited.append(current_group)

    # Enforce min chunk size by merging undersized groups into neighbors.
    i = 0
    while i < len(max_limited):
        group_len = len(" ".join(chunk_dicts[idx]["chunk"] for idx in max_limited[i]))
        if group_len >= min_chars or len(max_limited) == 1:
            i += 1
            continue
        if i == 0:
            max_limited[1] = max_limited[0] + max_limited[1]
            del max_limited[0]
            continue
        max_limited[i - 1] = max_limited[i - 1] + max_limited[i]
        del max_limited[i]
        i -= 1

    chunk_texts: list[str] = []
    for group_i, group in enumerate(max_limited):
        if not group:
            continue
        first_sentence_idx = group[0]
        chunk_start = sentence_spans[first_sentence_idx][0]
        if group_i < len(max_limited) - 1 and max_limited[group_i + 1]:
            next_first_sentence_idx = max_limited[group_i + 1][0]
            chunk_end = sentence_spans[next_first_sentence_idx][0]
        else:
            chunk_end = len(text)
        if chunk_end > chunk_start:
            chunk_texts.append(text[chunk_start:chunk_end])
    return chunks_with_offsets(text, chunk_texts)


def clustering_split(text: str, params: ChunkingParams) -> list[dict]:
    """Clustering (CRAG-style): sentences -> embeddings -> KMeans -> chunks (blog)."""
    import re
    from nltk.tokenize import sent_tokenize
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import KMeans

    try:
        sentences = sent_tokenize(text)
    except Exception:
        sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) < 2:
        return chunks_with_offsets(text, [text] if text.strip() else [])

    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(sentences, show_progress_bar=False)

    text_len = len(text)
    num_sentences = len(sentences)
    avg_chars_per_sent = text_len / num_sentences
    min_sentences = max(2, params.clustering_min / avg_chars_per_sent)
    if params.num_clusters is not None:
        num_clusters = params.num_clusters
    else:
        num_clusters = max(2, min(num_sentences // 2, int(num_sentences / min_sentences)))
    num_clusters = min(num_clusters, num_sentences)

    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings)
    # Keep chunks contiguous in document order so offsets map to a visible region.
    chunk_texts = []
    current_chunk = [sentences[0]]
    current_cluster = clusters[0]
    for i in range(1, len(sentences)):
        if clusters[i] != current_cluster:
            chunk_texts.append(" ".join(current_chunk))
            current_chunk = []
            current_cluster = clusters[i]
        current_chunk.append(sentences[i])
    chunk_texts.append(" ".join(current_chunk))
    return chunks_with_offsets(text, chunk_texts)


def llm_split(text: str, params: ChunkingParams) -> list[dict]:
    """
    LLM-based (agent assisted) chunking.
    Blog uses propositions via Gemini; here we use paragraph-based splitting
    unless OPENAI_API_KEY or GOOGLE_API_KEY is set for real LLM chunking.
    """
    # Optional: call LLM if API key present (e.g. OpenAI/Gemini for propositions)
    # For visualization we use paragraph-based splitting as a stand-in
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return chunks_with_offsets(text, [text] if text.strip() else [])

    chunk_texts = []
    current = []
    current_len = 0
    for p in paragraphs:
        if current_len + len(p) > params.llm_max and current:
            chunk_texts.append("\n\n".join(current))
            current = []
            current_len = 0
        current.append(p)
        current_len += len(p)
    if current:
        chunk_texts.append("\n\n".join(current))
    return chunks_with_offsets(text, chunk_texts)


def html_header_split(text: str, params: ChunkingParams) -> list[dict]:
    """LangChain HTML header-based splitting (article)."""
    splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2"), ("h3", "Header 3")]
    )
    docs = splitter.split_text(text)
    chunks = [doc.page_content for doc in docs if doc.page_content.strip()]
    return chunks_with_offsets(text, chunks)


def markdown_header_split(text: str, params: ChunkingParams) -> list[dict]:
    """LangChain Markdown header-based splitting (#, ##, ###)."""
    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")],
        strip_headers=False,
    )
    docs = splitter.split_text(text)
    chunks = [doc.page_content for doc in docs if doc.page_content.strip()]
    return chunks_with_offsets(text, chunks)


def code_split(text: str, params: ChunkingParams) -> list[dict]:
    """LangChain code-aware splitting (article)."""
    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=params.code_chunk_size,
        chunk_overlap=params.code_chunk_overlap,
    )
    chunks = splitter.split_text(text)
    return chunks_with_offsets(text, chunks)


def recursive_json_split(text: str, params: ChunkingParams) -> list[dict]:
    """LangChain recursive JSON splitting (article)."""
    splitter = RecursiveJsonSplitter(max_chunk_size=params.json_max_chunk_size)
    try:
        json_obj = json.loads(text)
    except json.JSONDecodeError:
        json_obj = {"text": text}
    chunks = splitter.split_text(json_data=json_obj)
    if isinstance(chunks, list):
        chunk_texts = [
            chunk if isinstance(chunk, str) else json.dumps(chunk, ensure_ascii=True)
            for chunk in chunks
        ]
    else:
        chunk_texts = [text]
    return chunks_with_offsets(text, chunk_texts)


def _llama_nodes_to_chunks(text: str, nodes: list) -> list[dict]:
    chunk_texts: list[str] = []
    for node in nodes:
        node_text = getattr(node, "text", None)
        if not node_text and hasattr(node, "get_content"):
            node_text = node.get_content()
        if node_text and node_text.strip():
            chunk_texts.append(node_text)
    return chunks_with_offsets(text, chunk_texts)


def _find_line_in_text(text: str, line: str, search_from: int) -> int:
    """Find a line in text, returning its start position or -1."""
    stripped = line.strip()
    if not stripped:
        return -1
    return text.find(stripped, search_from)


def _find_chunk_offsets(
    text: str, chunk_text: str, search_from: int
) -> tuple[int, int]:
    """Find where a chunk's content appears in the original text.

    Handles cases where chunk_text has been transformed (e.g. ## headers
    stripped by MarkdownElementNodeParser). Walks through all non-empty
    lines sequentially to handle repeated lines (e.g. "Published: 17 May
    2023" appearing multiple times in the same section).
    """
    lines = [l for l in chunk_text.split("\n") if l.strip()]
    if not lines:
        return search_from, search_from

    # Find the first content line in original text
    first_pos = _find_line_in_text(text, lines[0], search_from)
    if first_pos == -1:
        return search_from, search_from + len(chunk_text)

    # Expand start to the beginning of that line (to include ## prefix etc.)
    start = first_pos
    while start > 0 and text[start - 1] != "\n":
        start -= 1

    # Walk through ALL lines in order to find the correct last position.
    # This handles repeated lines by matching each at its sequential occurrence.
    cursor = first_pos + len(lines[0].strip())
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        pos = text.find(stripped, cursor)
        if pos == -1:
            break
        cursor = pos + len(stripped)

    end = cursor

    # Expand end past trailing whitespace/newlines up to the next content
    while end < len(text) and text[end] in " \t":
        end += 1
    if end < len(text) and text[end] == "\n":
        end += 1

    return start, end


def element_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex MarkdownElementNodeParser: keeps tables/lists/code blocks intact.

    Matches the approach from generate_goldens.py:
    1. Split by markdown headers first (preserves section context)
    2. For each section, extract structural elements (tables, lists, code blocks)
    3. Convert table elements to their HTML representation

    Offsets are computed by finding each element's content lines in the
    original text, expanding to line boundaries to handle stripped markdown
    formatting (e.g. ## headers removed by extract_elements).
    """
    from llama_index.core.node_parser import MarkdownElementNodeParser

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")],
        strip_headers=False,
    )
    section_docs = header_splitter.split_text(text)

    element_parser = MarkdownElementNodeParser()
    result: list[dict] = []
    chunk_index = 0
    doc_cursor = 0  # track position across sections

    for section_doc in section_docs:
        section_text = section_doc.page_content.strip()
        if not section_text:
            continue

        # Find where this section starts by its first line (header)
        first_line = section_text.split("\n", 1)[0].strip()
        section_start = text.find(first_line, doc_cursor)
        if section_start == -1:
            section_start = doc_cursor

        elements = element_parser.extract_elements(
            section_text, table_filters=[element_parser.filter_table]
        )
        elements = element_parser.extract_html_tables(elements)
        if not elements:
            doc_cursor = section_start + len(first_line)
            continue

        el_cursor = section_start
        for el in elements:
            chunk_text = str(el.element).strip()
            if not chunk_text:
                continue

            start, end = _find_chunk_offsets(text, chunk_text, el_cursor)

            # Use the original text at the computed offsets so that
            # markdown formatting (## headers etc.) is preserved in display.
            display_text = text[start:end].strip() or chunk_text

            result.append({
                "index": chunk_index,
                "text": display_text,
                "startOffset": start,
                "endOffset": end,
            })
            chunk_index += 1
            el_cursor = end

        doc_cursor = el_cursor

    return result


def llama_markdown_node_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex Markdown node parsing (article)."""
    from llama_index.core import Document
    from llama_index.core.node_parser import MarkdownNodeParser

    parser = MarkdownNodeParser()
    nodes = parser.get_nodes_from_documents([Document(text=text)])
    return _llama_nodes_to_chunks(text, nodes)


def llama_html_node_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex HTML node parsing (article)."""
    from llama_index.core import Document
    from llama_index.core.node_parser import HTMLNodeParser

    parser = HTMLNodeParser(tags=["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"])
    nodes = parser.get_nodes_from_documents([Document(text=text)])
    return _llama_nodes_to_chunks(text, nodes)


def llama_sentence_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex sentence splitting (article)."""
    from llama_index.core import Document
    from llama_index.core.node_parser import SentenceSplitter

    parser = SentenceSplitter(
        chunk_size=params.llama_sentence_size,
        chunk_overlap=params.llama_sentence_overlap,
    )
    nodes = parser.get_nodes_from_documents([Document(text=text)])
    return _llama_nodes_to_chunks(text, nodes)


def llama_sentence_window_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex sentence-window node parsing (article)."""
    from llama_index.core import Document
    from llama_index.core.node_parser import SentenceWindowNodeParser

    parser = SentenceWindowNodeParser.from_defaults(
        window_size=params.llama_sentence_window_size
    )
    nodes = parser.get_nodes_from_documents([Document(text=text)])
    return _llama_nodes_to_chunks(text, nodes)


def llama_hierarchical_split(text: str, params: ChunkingParams) -> list[dict]:
    """LlamaIndex hierarchical node parsing (article)."""
    from llama_index.core import Document
    from llama_index.core.node_parser import HierarchicalNodeParser

    parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[
            params.llama_hierarchical_large,
            params.llama_hierarchical_medium,
            params.llama_hierarchical_small,
        ]
    )
    all_nodes = parser.get_nodes_from_documents([Document(text=text)])
    nodes = [node for node in all_nodes if not getattr(node, "child_nodes", None)]
    if not nodes:
        nodes = all_nodes
    return _llama_nodes_to_chunks(text, nodes)
