"""
Golden Dataset Generator - Unified CLI

Generate synthetic Q&A pairs from documents using different chunking strategies.

Usage:
    # Recursive chunking (default)
    python generate_goldens.py --strategy recursive --dump-chunks

    # LlamaIndex hierarchical chunking
    python generate_goldens.py --strategy hierarchical --dump-chunks

    # Markdown element-aware chunking (keeps tables/lists intact)
    python generate_goldens.py --strategy elements --dump-chunks

    # Only visualize chunks (skip golden generation)
    python generate_goldens.py --strategy recursive --dump-chunks --no-goldens

    # With MLflow tracking
    python generate_goldens.py --strategy recursive --mlflow
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from golden_utils import (
    build_section_path,
    dump_chunk_viewer,
    export_failure_report,
    export_goldens,
    find_document,
    generate_goldens,
    load_mlflow,
    log_mlflow_run,
    prefix_section,
)


# ============================================================================
# Chunking Strategies
# ============================================================================


def chunk_recursive(
    doc_path: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 150,
    contexts_per_section: int = 3,
    chunks_per_context: int = 2,
) -> Dict[str, Any]:
    """
    Header-aware recursive chunking.

    Splits by markdown headers first, then applies recursive character splitting
    within each section. Good general-purpose strategy.
    """
    text = Path(doc_path).read_text(encoding="utf-8")
    print(f"Document: {doc_path} ({len(text):,} chars)")

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")],
        strip_headers=False,
    )
    section_docs = header_splitter.split_text(text)
    print(f"Header sections: {len(section_docs)}")

    inner_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    sections_out = []
    contexts = []

    for section_doc in section_docs:
        section_path = build_section_path(section_doc.metadata)
        section_text = section_doc.page_content.strip()
        if not section_text:
            continue

        raw_chunks = inner_splitter.split_text(section_text)
        chunks = [c.strip() for c in raw_chunks if c.strip()]
        if not chunks:
            continue

        prefixed = [prefix_section(section_path, c) for c in chunks]
        sections_out.append({"section": section_path or "(no headers)", "chunks": prefixed})

        for i in range(min(len(chunks), contexts_per_section)):
            ctx = prefixed[i : i + chunks_per_context]
            if ctx:
                contexts.append(ctx)

    print(f"Sections: {len(sections_out)}, Contexts: {len(contexts)}")
    return {"sections": sections_out, "contexts": contexts}


def chunk_hierarchical(
    doc_path: str,
    parent_chunk_size: int = 2000,
    child_chunk_size: int = 800,
    contexts_per_section: int = 3,
    chunks_per_context: int = 2,
) -> Dict[str, Any]:
    """
    Hierarchical chunking with parent-child relationships.

    1. Splits by markdown headers first (preserves section context)
    2. Creates parent chunks (larger) and child chunks (smaller) within each section
    3. Contexts include parent chunk + child chunks for richer retrieval

    Useful for RAG systems that benefit from hierarchical context.
    """
    text = Path(doc_path).read_text(encoding="utf-8")
    print(f"Document: {doc_path} ({len(text):,} chars)")

    # Step 1: Split by headers (preserves h1/h2/h3/h4 metadata)
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")],
        strip_headers=False,
    )
    section_docs = header_splitter.split_text(text)
    print(f"Header sections: {len(section_docs)}")

    # Step 2: Create parent and child splitters
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_chunk_size,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_chunk_size,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    sections_out = []
    contexts = []
    seen = set()

    for section_doc in section_docs:
        section_path = build_section_path(section_doc.metadata)
        section_text = section_doc.page_content.strip()
        if not section_text:
            continue

        # Create parent chunks for this section
        parent_chunks = parent_splitter.split_text(section_text)
        parent_chunks = [p.strip() for p in parent_chunks if p.strip()]

        if not parent_chunks:
            continue

        # For each parent, create child chunks
        all_chunks_for_section = []
        for parent_text in parent_chunks:
            child_chunks = child_splitter.split_text(parent_text)
            child_chunks = [c.strip() for c in child_chunks if c.strip()]

            # If parent is small enough, it becomes its own chunk
            if not child_chunks or (len(child_chunks) == 1 and child_chunks[0] == parent_text):
                prefixed_parent = prefix_section(section_path, parent_text)
                all_chunks_for_section.append(prefixed_parent)

                # Context: just the parent
                ctx = [prefixed_parent]
                key = tuple(ctx)
                if key not in seen:
                    seen.add(key)
                    contexts.append(ctx)
            else:
                # Add child chunks to section
                prefixed_children = [prefix_section(section_path, c) for c in child_chunks]
                all_chunks_for_section.extend(prefixed_children)

                # Context: parent + sliding window of children
                prefixed_parent = prefix_section(section_path, parent_text)
                for i in range(min(len(child_chunks), contexts_per_section)):
                    group = prefixed_children[i : i + chunks_per_context]
                    if not group:
                        continue
                    # Include parent for broader context, then children for specifics
                    ctx = [prefixed_parent] + group
                    key = tuple(ctx)
                    if key not in seen:
                        seen.add(key)
                        contexts.append(ctx)

        if all_chunks_for_section:
            sections_out.append({
                "section": section_path or "(no headers)",
                "chunks": all_chunks_for_section,
            })

    print(f"Sections: {len(sections_out)}, Contexts: {len(contexts)}")
    return {"sections": sections_out, "contexts": contexts}


def chunk_elements(
    doc_path: str,
    contexts_per_section: int = 3,
    chunks_per_context: int = 2,
) -> Dict[str, Any]:
    """
    Markdown element-aware chunking using LlamaIndex MarkdownElementNodeParser.

    Keeps tables, lists, and code blocks intact as single chunks.
    Best for documents with structured content.
    """
    try:
        from llama_index.core.node_parser import MarkdownElementNodeParser
    except ImportError as exc:
        raise RuntimeError("Install llama-index: pip install llama-index") from exc

    text = Path(doc_path).read_text(encoding="utf-8")
    print(f"Document: {doc_path} ({len(text):,} chars)")

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h4")],
        strip_headers=False,
    )
    section_docs = header_splitter.split_text(text)
    print(f"Header sections: {len(section_docs)}")

    element_parser = MarkdownElementNodeParser()

    section_order = []
    section_chunks: Dict[str, List[str]] = {}

    for section_doc in section_docs:
        section_path = build_section_path(section_doc.metadata)
        section_text = section_doc.page_content.strip()
        if not section_text:
            continue

        elements = element_parser.extract_elements(
            section_text, table_filters=[element_parser.filter_table]
        )
        elements = element_parser.extract_html_tables(elements)
        if not elements:
            continue

        for element in elements:
            chunk = str(element.element).strip()
            if not chunk:
                continue
            name = section_path or "(no headers)"
            if name not in section_chunks:
                section_chunks[name] = []
                section_order.append(name)
            section_chunks[name].append(prefix_section(section_path, chunk))

    sections_out = []
    contexts = []

    for name in section_order:
        chunks = section_chunks.get(name, [])
        if not chunks:
            continue
        sections_out.append({"section": name, "chunks": chunks})

        for i in range(min(len(chunks), contexts_per_section)):
            ctx = chunks[i : i + chunks_per_context]
            if ctx:
                contexts.append(ctx)

    print(f"Sections: {len(sections_out)}, Contexts: {len(contexts)}")
    return {"sections": sections_out, "contexts": contexts}


# ============================================================================
# Strategy Registry
# ============================================================================

STRATEGIES = {
    "recursive": chunk_recursive,
    "hierarchical": chunk_hierarchical,
    "elements": chunk_elements,
}


# ============================================================================
# Main Pipeline
# ============================================================================


def run_pipeline(args) -> Dict[str, Any]:
    """Run the full chunking and golden generation pipeline."""
    doc_path = find_document(args.doc_path)
    print(f"Using document: {doc_path}\n")

    strategy_fn = STRATEGIES[args.strategy]

    # Build kwargs based on strategy
    if args.strategy == "recursive":
        result = strategy_fn(
            doc_path,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            contexts_per_section=args.contexts_per_section,
            chunks_per_context=args.chunks_per_context,
        )
    elif args.strategy == "hierarchical":
        result = strategy_fn(
            doc_path,
            parent_chunk_size=args.parent_chunk_size,
            child_chunk_size=args.child_chunk_size,
            contexts_per_section=args.contexts_per_section,
            chunks_per_context=args.chunks_per_context,
        )
    else:  # elements
        result = strategy_fn(
            doc_path,
            contexts_per_section=args.contexts_per_section,
            chunks_per_context=args.chunks_per_context,
        )

    sections = result["sections"]
    contexts = result["contexts"][: args.max_contexts]
    print(f"\nUsing {len(contexts)} contexts for golden generation")

    viewer_path = None
    if args.dump_chunks:
        viewer_path = str(Path(args.dump_dir) / f"chunks_{args.strategy}.md")
        dump_chunk_viewer(sections, contexts, viewer_path)

    if args.no_goldens:
        print("\nSkipping golden generation (--no-goldens). Done.")
        return {
            "doc_path": doc_path,
            "strategy": args.strategy,
            "sections": sections,
            "contexts": contexts,
            "viewer_path": viewer_path,
            "goldens_path": None,
            "goldens_count": None,
        }

    gen_result = generate_goldens(
        contexts,
        max_goldens_per_context=args.goldens_per_context,
        auto_resume=not args.fresh,
        model_name=args.model_name,
        quantization=args.quantization,
        gpu_memory_utilization=args.gpu_memory_utilization,
    )
    goldens = gen_result["goldens"]

    for i, g in enumerate(goldens[:5], 1):
        print(f"\n--- Golden {i} ---")
        q = g["input"] if isinstance(g, dict) else g.input
        a = (g["expected_output"] if isinstance(g, dict) else g.expected_output) or ""
        print(f"Q: {q}")
        print(f"A: {a[:150]}..." if len(a) > 150 else f"A: {a}")

    output_name = f"goldens_{args.strategy}.json"
    goldens_path = export_goldens(goldens, output_name=output_name)
    print(f"\nSaved to: {goldens_path}")

    # Export failure report if there were failures
    failure_report_path = None
    if gen_result["failures"]:
        failure_report_path = export_failure_report(
            gen_result["failures"],
            output_name=f"failure_report_{args.strategy}.md",
        )

    return {
        "doc_path": doc_path,
        "strategy": args.strategy,
        "sections": sections,
        "contexts": contexts,
        "viewer_path": viewer_path,
        "goldens_path": goldens_path,
        "goldens_count": len(goldens),
        "failed_count": gen_result["failed_count"],
        "failed_indices": gen_result["failed_indices"],
        "failures": gen_result["failures"],
        "checkpoint_path": gen_result["checkpoint_path"],
        "failure_report_path": failure_report_path,
        "model_info": gen_result.get("model_info"),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate golden Q&A datasets with configurable chunking strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_goldens.py --strategy recursive --dump-chunks
  python generate_goldens.py --strategy hierarchical --max-contexts 20
  python generate_goldens.py --strategy elements --no-goldens --dump-chunks

  # If a run fails, just re-run - it auto-resumes from checkpoints/goldens.json
  # To start over completely:
  python generate_goldens.py --strategy recursive --fresh
        """,
    )

    # Core options
    parser.add_argument(
        "--strategy",
        choices=list(STRATEGIES.keys()),
        default="recursive",
        help="Chunking strategy: recursive (default), hierarchical, or elements",
    )
    parser.add_argument("--doc-path", type=str, help="Path to input document")

    # Shared chunking params
    parser.add_argument("--contexts-per-section", type=int, default=3)
    parser.add_argument("--chunks-per-context", type=int, default=2)
    parser.add_argument("--max-contexts", type=int, default=12)

    # Recursive strategy params
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=150)

    # Hierarchical strategy params
    parser.add_argument("--parent-chunk-size", type=int, default=2000)
    parser.add_argument("--child-chunk-size", type=int, default=800)

    # Output options
    parser.add_argument("--dump-chunks", action="store_true", help="Export chunk visualization")
    parser.add_argument("--dump-dir", type=str, default="chunk_view")
    parser.add_argument("--no-goldens", action="store_true", help="Skip golden generation")
    parser.add_argument("--goldens-per-context", type=int, default=2, help="Goldens to generate per context")

    # Checkpoint options
    parser.add_argument("--fresh", action="store_true",
                        help="Start fresh, ignoring any existing checkpoint")

    # Model options
    parser.add_argument("--model-name", type=str,
                        default="Qwen/Qwen2.5-7B-Instruct-GPTQ-Int4",
                        help="vLLM model to use for generation")
    parser.add_argument("--quantization", type=str, default=None,
                        help="Quantization method (gptq, awq, etc.). Leave empty for pre-quantized models.")
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.75,
                        help="GPU memory utilization (0.0-1.0)")

    # MLflow options
    parser.add_argument("--mlflow", action="store_true", help="Enable MLflow tracking")
    parser.add_argument("--mlflow-uri", type=str, help="MLflow tracking URI")
    parser.add_argument("--mlflow-exp", type=str, default="rag-chunking")
    parser.add_argument("--mlflow-run-name", type=str)

    args = parser.parse_args()

    # Auto-detect quantization if not specified
    if args.quantization is None:
        if "GPTQ" in args.model_name or "gptq" in args.model_name.lower():
            args.quantization = "gptq"
            print(f"Auto-detected quantization: gptq")
        elif "AWQ" in args.model_name or "awq" in args.model_name.lower():
            args.quantization = "awq"
            print(f"Auto-detected quantization: awq")
        # For bitsandbytes or other pre-quantized models, leave as None
        else:
            print(f"No quantization specified (using model's built-in quantization)")

    mlflow = load_mlflow(args.mlflow)
    if not mlflow:
        run_pipeline(args)
        return

    if args.mlflow_uri:
        mlflow.set_tracking_uri(args.mlflow_uri)
    mlflow.set_experiment(args.mlflow_exp)

    with mlflow.start_run(run_name=args.mlflow_run_name):
        result = run_pipeline(args)
        command_line = " ".join(sys.argv)
        log_mlflow_run(
            mlflow,
            strategy=result["strategy"],
            doc_path=result["doc_path"],
            sections=result["sections"],
            contexts=result["contexts"],
            goldens_count=result["goldens_count"],
            failed_count=result.get("failed_count", 0),
            viewer_path=result["viewer_path"],
            goldens_path=result["goldens_path"],
            checkpoint_path=result.get("checkpoint_path"),
            failure_report_path=result.get("failure_report_path"),
            script_path=__file__,
            command_line=command_line,
            model_info=result.get("model_info"),
            extra_params={
                "chunk_size": args.chunk_size,
                "chunk_overlap": args.chunk_overlap,
                "contexts_per_section": args.contexts_per_section,
                "max_contexts": args.max_contexts,
                "goldens_per_context": args.goldens_per_context,
                "fresh": args.fresh,
                "model_name": args.model_name,
                "quantization": args.quantization,
                "gpu_memory_utilization": args.gpu_memory_utilization,
            },
        )


if __name__ == "__main__":
    main()