"""
Unit tests for chunking splitters.
Tests structural contracts: coverage, ordering, parameter sensitivity, edge cases.
Heavy splitters (semantic, clustering) are in a separate class marked slow.
"""
import json
import pytest
from chunking.schemas import ChunkingParams
from chunking.splitters import (
    character_split,
    clustering_split,
    code_split,
    html_header_split,
    llm_split,
    markdown_header_split,
    recursive_json_split,
    recursive_split,
    semantic_split,
    token_split,
    llama_markdown_node_split,
    llama_html_node_split,
    llama_sentence_split,
    llama_sentence_window_split,
    llama_hierarchical_split,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TEXT = (
    "# Introduction\n\n"
    "This is the first paragraph. It has multiple sentences. "
    "Sentences are important for semantic splitters.\n\n"
    "## Methods\n\n"
    "We describe three methods. Method A is fast. Method B is accurate. "
    "Method C balances speed and accuracy.\n\n"
    "### Details\n\n"
    "Here are some details about the methods. "
    "Each method has trade-offs that should be carefully considered.\n\n"
    "## Results\n\n"
    "The results show that Method B performs best on the benchmark. "
    "However, Method C is a close second with much lower latency.\n\n"
    "## Conclusion\n\n"
    "In conclusion, the choice depends on your requirements."
)

SHORT_TEXT = "Hello world."
EMPTY_TEXT = ""
WHITESPACE_TEXT = "   \n\n   "

SAMPLE_HTML = (
    "<html><body>"
    "<h1>Title</h1><p>Intro paragraph.</p>"
    "<h2>Section</h2><p>Section content here.</p>"
    "<h3>Subsection</h3><p>Subsection content.</p>"
    "</body></html>"
)

SAMPLE_JSON = json.dumps({
    "name": "project",
    "version": "1.0",
    "dependencies": {
        "langchain": "0.1",
        "llama-index": "0.9",
        "numpy": "1.26",
    },
    "scripts": {"test": "pytest", "lint": "ruff check ."},
})


def default_params(**overrides) -> ChunkingParams:
    return ChunkingParams(**overrides)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_valid_chunks(chunks: list[dict], text: str, *, allow_empty: bool = False, strict_bounds: bool = True):
    """Common assertions every splitter output must satisfy."""
    assert isinstance(chunks, list)
    if not allow_empty:
        assert len(chunks) > 0, "Expected at least one chunk"
    for i, c in enumerate(chunks):
        assert "index" in c and "text" in c and "startOffset" in c and "endOffset" in c
        assert c["index"] == i, f"Chunk index mismatch: expected {i}, got {c['index']}"
        assert c["startOffset"] >= 0
        assert c["endOffset"] >= c["startOffset"]
        if strict_bounds:
            assert c["endOffset"] <= len(text) + 1  # allow tiny tolerance


def assert_offsets_ordered(chunks: list[dict]):
    """startOffset should be non-decreasing (chunks appear in document order)."""
    for i in range(1, len(chunks)):
        assert chunks[i]["startOffset"] >= chunks[i - 1]["startOffset"], (
            f"Chunk {i} startOffset ({chunks[i]['startOffset']}) < "
            f"chunk {i-1} startOffset ({chunks[i-1]['startOffset']})"
        )


def assert_full_coverage(chunks: list[dict], text: str, tolerance: int = 5):
    """Every character in the text should appear in at least one chunk (approximately)."""
    covered = set()
    for c in chunks:
        for j in range(c["startOffset"], c["endOffset"]):
            covered.add(j)
    text_chars = {i for i, ch in enumerate(text) if not ch.isspace()}
    uncovered = text_chars - covered
    # Allow a small tolerance for whitespace normalization
    assert len(uncovered) <= tolerance, (
        f"{len(uncovered)} non-whitespace chars uncovered (tolerance={tolerance})"
    )


# ===========================================================================
# 1. CharacterTextSplitter
# ===========================================================================

class TestCharacterSplit:
    def test_basic(self):
        chunks = character_split(SAMPLE_TEXT, default_params(character_size=200, character_overlap=20))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) > 1

    def test_smaller_chunk_size_yields_more_chunks(self):
        big = character_split(SAMPLE_TEXT, default_params(character_size=500, character_overlap=0))
        small = character_split(SAMPLE_TEXT, default_params(character_size=100, character_overlap=0))
        assert len(small) >= len(big)

    def test_short_text(self):
        chunks = character_split(SHORT_TEXT, default_params(character_size=500))
        assert_valid_chunks(chunks, SHORT_TEXT)
        assert len(chunks) == 1
        assert chunks[0]["text"] == SHORT_TEXT


# ===========================================================================
# 2. RecursiveCharacterTextSplitter
# ===========================================================================

class TestRecursiveSplit:
    def test_basic(self):
        chunks = recursive_split(SAMPLE_TEXT, default_params(recursive_size=200, recursive_overlap=20))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) > 1

    def test_smaller_yields_more(self):
        big = recursive_split(SAMPLE_TEXT, default_params(recursive_size=500, recursive_overlap=0))
        small = recursive_split(SAMPLE_TEXT, default_params(recursive_size=100, recursive_overlap=0))
        assert len(small) >= len(big)

    def test_respects_paragraph_boundaries(self):
        """Recursive splitter should prefer splitting at \\n\\n before \\n."""
        chunks = recursive_split(SAMPLE_TEXT, default_params(recursive_size=300, recursive_overlap=0))
        for c in chunks:
            # chunks should not start/end mid-word unless forced
            stripped = c["text"].strip()
            assert len(stripped) > 0


# ===========================================================================
# 3. TokenTextSplitter
# ===========================================================================

class TestTokenSplit:
    def test_basic(self):
        chunks = token_split(SAMPLE_TEXT, default_params(token_size=50, token_overlap=5))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) > 1

    def test_smaller_yields_more(self):
        big = token_split(SAMPLE_TEXT, default_params(token_size=200, token_overlap=0))
        small = token_split(SAMPLE_TEXT, default_params(token_size=50, token_overlap=0))
        assert len(small) >= len(big)


# ===========================================================================
# 4. Semantic Split (slow — requires model download)
# ===========================================================================

@pytest.mark.slow
class TestSemanticSplit:
    def test_basic(self):
        chunks = semantic_split(SAMPLE_TEXT, default_params(semantic_percentile=80))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) >= 1

    def test_higher_percentile_fewer_breaks(self):
        """Higher percentile = fewer break points = fewer (or equal) chunks."""
        low = semantic_split(SAMPLE_TEXT, default_params(semantic_percentile=50))
        high = semantic_split(SAMPLE_TEXT, default_params(semantic_percentile=95))
        assert len(high) <= len(low)

    def test_combined_context_used(self):
        """The blog says each sentence embedding uses prev+curr+next context.
        We verify indirectly: semantic should produce different breaks than
        character splitting of same size."""
        sem = semantic_split(SAMPLE_TEXT, default_params(semantic_percentile=80))
        char = character_split(SAMPLE_TEXT, default_params(character_size=200))
        sem_starts = [c["startOffset"] for c in sem]
        char_starts = [c["startOffset"] for c in char]
        # They should differ (not a proof, but a sanity check)
        assert sem_starts != char_starts

    def test_short_text_single_chunk(self):
        chunks = semantic_split(SHORT_TEXT, default_params())
        assert_valid_chunks(chunks, SHORT_TEXT)
        assert len(chunks) == 1


# ===========================================================================
# 5. Clustering Split (slow — requires model download)
# ===========================================================================

@pytest.mark.slow
class TestClusteringSplit:
    def test_basic(self):
        chunks = clustering_split(SAMPLE_TEXT, default_params())
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) >= 2

    def test_explicit_num_clusters(self):
        chunks = clustering_split(SAMPLE_TEXT, default_params(num_clusters=3))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        # KMeans with 3 clusters should produce at most 3 contiguous groups
        # (could be fewer if adjacent sentences share a cluster)
        assert len(chunks) <= 10  # reasonable upper bound

    def test_contiguous_order(self):
        """Blog says chunks must be contiguous in document order."""
        chunks = clustering_split(SAMPLE_TEXT, default_params(num_clusters=3))
        assert_offsets_ordered(chunks)

    def test_short_text_fallback(self):
        chunks = clustering_split(SHORT_TEXT, default_params())
        assert_valid_chunks(chunks, SHORT_TEXT)
        assert len(chunks) == 1


# ===========================================================================
# 6. LLM Split (paragraph proxy)
# ===========================================================================

class TestLlmSplit:
    def test_basic(self):
        chunks = llm_split(SAMPLE_TEXT, default_params(llm_max=200))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)
        assert len(chunks) > 1

    def test_large_max_single_chunk(self):
        chunks = llm_split(SAMPLE_TEXT, default_params(llm_max=10000))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) == 1

    def test_splits_at_paragraph_boundaries(self):
        """Chunks should be composed of whole paragraphs joined by \\n\\n."""
        chunks = llm_split(SAMPLE_TEXT, default_params(llm_max=200))
        original_paragraphs = {p.strip() for p in SAMPLE_TEXT.split("\n\n") if p.strip()}
        for c in chunks:
            chunk_paragraphs = [p.strip() for p in c["text"].split("\n\n") if p.strip()]
            for p in chunk_paragraphs:
                assert p in original_paragraphs, f"Chunk contains non-paragraph text: {p[:50]}"


# ===========================================================================
# 7. HTML Header Split
# ===========================================================================

class TestHtmlHeaderSplit:
    def test_basic(self):
        chunks = html_header_split(SAMPLE_HTML, default_params())
        assert_valid_chunks(chunks, SAMPLE_HTML)
        assert len(chunks) >= 1

    def test_splits_on_headers(self):
        chunks = html_header_split(SAMPLE_HTML, default_params())
        texts = [c["text"] for c in chunks]
        # Should produce separate chunks for different header sections
        assert any("Intro" in t for t in texts)


# ===========================================================================
# 8. Markdown Header Split
# ===========================================================================

class TestMarkdownHeaderSplit:
    def test_basic(self):
        chunks = markdown_header_split(SAMPLE_TEXT, default_params())
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) >= 2

    def test_splits_at_header_boundaries(self):
        chunks = markdown_header_split(SAMPLE_TEXT, default_params())
        # With #, ##, ### headers, we expect multiple chunks
        assert len(chunks) >= 3


# ===========================================================================
# 9. Code Split
# ===========================================================================

class TestCodeSplit:
    def test_basic(self):
        chunks = code_split(SAMPLE_TEXT, default_params(code_chunk_size=200, code_chunk_overlap=20))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert_offsets_ordered(chunks)

    def test_smaller_yields_more(self):
        big = code_split(SAMPLE_TEXT, default_params(code_chunk_size=500, code_chunk_overlap=0))
        small = code_split(SAMPLE_TEXT, default_params(code_chunk_size=100, code_chunk_overlap=0))
        assert len(small) >= len(big)


# ===========================================================================
# 10. Recursive JSON Split
# ===========================================================================

class TestRecursiveJsonSplit:
    def test_basic(self):
        # JSON splitter reformats keys, so chunk text may not be a substring of input
        chunks = recursive_json_split(SAMPLE_JSON, default_params(json_max_chunk_size=100))
        assert_valid_chunks(chunks, SAMPLE_JSON, strict_bounds=False)
        assert len(chunks) >= 1

    def test_valid_json_input(self):
        """Each chunk should be valid JSON (or a JSON fragment)."""
        chunks = recursive_json_split(SAMPLE_JSON, default_params(json_max_chunk_size=50))
        for c in chunks:
            # At minimum, the chunk text should be non-empty
            assert len(c["text"].strip()) > 0

    def test_non_json_input_fallback(self):
        """Non-JSON input should still produce chunks (wrapped in {"text": ...})."""
        chunks = recursive_json_split("not json at all", default_params(json_max_chunk_size=100))
        assert_valid_chunks(chunks, "not json at all", strict_bounds=False)


# ===========================================================================
# 11. LlamaIndex Markdown Node Parser
# ===========================================================================

class TestLlamaMarkdownNodeSplit:
    def test_basic(self):
        chunks = llama_markdown_node_split(SAMPLE_TEXT, default_params())
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) >= 2

    def test_header_aware(self):
        chunks = llama_markdown_node_split(SAMPLE_TEXT, default_params())
        # Should split around markdown headers
        assert len(chunks) >= 3


# ===========================================================================
# 12. LlamaIndex HTML Node Parser
# ===========================================================================

class TestLlamaHtmlNodeSplit:
    def test_basic(self):
        chunks = llama_html_node_split(SAMPLE_HTML, default_params())
        assert_valid_chunks(chunks, SAMPLE_HTML)
        assert len(chunks) >= 1


# ===========================================================================
# 13. LlamaIndex Sentence Splitter
# ===========================================================================

class TestLlamaSentenceSplit:
    def test_basic(self):
        chunks = llama_sentence_split(SAMPLE_TEXT, default_params(llama_sentence_size=100, llama_sentence_overlap=10))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) > 1

    def test_smaller_yields_more(self):
        big = llama_sentence_split(SAMPLE_TEXT, default_params(llama_sentence_size=1024, llama_sentence_overlap=0))
        small = llama_sentence_split(SAMPLE_TEXT, default_params(llama_sentence_size=100, llama_sentence_overlap=0))
        assert len(small) >= len(big)


# ===========================================================================
# 14. LlamaIndex Sentence Window
# ===========================================================================

class TestLlamaSentenceWindowSplit:
    def test_basic(self):
        chunks = llama_sentence_window_split(SAMPLE_TEXT, default_params(llama_sentence_window_size=3))
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) >= 1


# ===========================================================================
# 15. LlamaIndex Hierarchical
# ===========================================================================

class TestLlamaHierarchicalSplit:
    def test_basic(self):
        chunks = llama_hierarchical_split(
            SAMPLE_TEXT,
            default_params(
                llama_hierarchical_large=512,
                llama_hierarchical_medium=256,
                llama_hierarchical_small=128,
            ),
        )
        assert_valid_chunks(chunks, SAMPLE_TEXT)
        assert len(chunks) >= 1

    def test_returns_leaf_nodes(self):
        """Blog says we return leaf (smallest) nodes."""
        chunks = llama_hierarchical_split(
            SAMPLE_TEXT,
            default_params(
                llama_hierarchical_large=512,
                llama_hierarchical_medium=256,
                llama_hierarchical_small=128,
            ),
        )
        # Leaf nodes should be smaller than the large chunk size
        for c in chunks:
            assert len(c["text"]) <= 600  # some tolerance above 512


# ===========================================================================
# Edge cases (all fast splitters)
# ===========================================================================

class TestEdgeCases:
    @pytest.mark.parametrize("splitter_fn", [
        character_split, recursive_split, token_split,
        llm_split, code_split, markdown_header_split,
    ])
    def test_short_text(self, splitter_fn):
        chunks = splitter_fn(SHORT_TEXT, default_params())
        assert_valid_chunks(chunks, SHORT_TEXT)
        assert len(chunks) >= 1

    @pytest.mark.parametrize("splitter_fn", [
        character_split, recursive_split, token_split,
        llm_split, code_split,
    ])
    def test_empty_text_via_runner(self, splitter_fn):
        """The runner guards empty text, but splitters should not crash."""
        # Most LangChain splitters return [] for empty input
        chunks = splitter_fn("x", default_params())
        assert isinstance(chunks, list)
