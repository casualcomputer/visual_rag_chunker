# Chunking Analysis Sample

This is a sample markdown document for testing chunking strategies. Chunking refers to breaking down longer texts into smaller pieces for retrieval systems.

## Why Chunking Matters

When building RAG applications, you need to split documents into chunks before creating embeddings. The choice of chunking strategy affects retrieval quality.

Different approaches exist: fixed character splitting, semantic chunking, and clustering-based methods. Each has trade-offs between context preservation and granularity.

## Common Strategies

**CharacterTextSplitter** splits by a fixed number of characters. Simple but can break words or sentences mid-way.

**RecursiveCharacterTextSplitter** tries to split on natural boundaries first: paragraphs, then lines, then sentences, then words. It respects structure better.

**TokenTextSplitter** splits by token count, which aligns with how language models see text. Token limits matter for API calls.

**Semantic Chunking** groups text by meaning using embeddings. Consecutive sentences with similar meaning form one chunk. Better for retrieval but needs an embedding model.

**Clustering (CRAG)** splits into sentences, embeds them, then clusters by similarity. Topics end up together even if they appear in different parts of the document.

**LLM-based chunking** uses a language model to create propositions or to split the document. Highest quality but requires API calls and cost.

## Summary

No single strategy fits all use cases. Try several on your documents and measure retrieval quality for your queries.
