import type { ChunkingOption } from './types';

export const CHUNKING_OPTIONS: ChunkingOption[] = [
  {
    id: 'character',
    label: 'CharacterTextSplitter',
    description: 'Splits by a fixed number of characters.',
    params: [
      { key: 'characterSize', label: 'Chunk size', default: 500, min: 100, max: 2000 },
      { key: 'characterOverlap', label: 'Overlap', default: 50, min: 0, max: 200 },
    ],
  },
  {
    id: 'recursive',
    label: 'RecursiveCharacterTextSplitter',
    description: 'Splits on paragraphs, then lines, then sentences, then words.',
    params: [
      { key: 'recursiveSize', label: 'Chunk size', default: 500, min: 100, max: 2000 },
      { key: 'recursiveOverlap', label: 'Overlap', default: 50, min: 0, max: 200 },
    ],
  },
  {
    id: 'token',
    label: 'TokenTextSplitter',
    description: 'Splits by approximate token count (word-based heuristic).',
    params: [
      { key: 'tokenSize', label: 'Tokens per chunk', default: 256, min: 50, max: 512 },
      { key: 'tokenOverlap', label: 'Overlap (tokens)', default: 25, min: 0, max: 100 },
    ],
  },
  {
    id: 'semantic',
    label: 'Semantic Chunking',
    description: 'NLTK sentences + cosine similarity threshold (sequential semantic).',
    params: [
      { key: 'semanticMax', label: 'Max chunk chars', default: 800, min: 200, max: 2000 },
      { key: 'semanticMin', label: 'Min chunk chars', default: 100, min: 50, max: 500 },
      { key: 'semanticPercentile', label: 'Similarity threshold percentile', default: 90, min: 70, max: 99 },
    ],
  },
  {
    id: 'clustering',
    label: 'Clustering (CRAG-style)',
    description: 'Sentence embeddings + K-means clustering.',
    params: [
      { key: 'clusteringMax', label: 'Max chunk chars', default: 1200, min: 300, max: 3000 },
      { key: 'clusteringMin', label: 'Min chunk chars', default: 100, min: 50, max: 500 },
    ],
  },
  {
    id: 'llm',
    label: 'LLM-based (Agent assisted)',
    description: 'Paragraph-based proxy; real implementation would use an LLM API.',
    params: [{ key: 'llmMax', label: 'Max chunk chars', default: 600, min: 200, max: 1500 }],
  },
  {
    id: 'htmlHeader',
    label: 'HTML Header Splitter (LangChain)',
    description: 'Splits HTML content by header hierarchy (h1/h2/h3).',
  },
  {
    id: 'markdownHeader',
    label: 'Markdown Header Splitter (LangChain)',
    description: 'Splits Markdown content by header hierarchy (#/##/###).',
  },
  {
    id: 'code',
    label: 'Code Splitter (LangChain)',
    description: 'Code-aware recursive splitting (Markdown language rules).',
    params: [
      { key: 'codeChunkSize', label: 'Chunk size', default: 800, min: 200, max: 3000 },
      { key: 'codeChunkOverlap', label: 'Overlap', default: 50, min: 0, max: 400 },
    ],
  },
  {
    id: 'recursiveJson',
    label: 'Recursive JSON Splitter (LangChain)',
    description: 'Recursively splits JSON objects into size-bounded chunks.',
    params: [{ key: 'jsonMaxChunkSize', label: 'Max chunk size', default: 400, min: 100, max: 2000 }],
  },
  {
    id: 'llamaMarkdownNode',
    label: 'Markdown Node Parser (LlamaIndex)',
    description: 'Parses Markdown structure into nodes/chunks.',
  },
  {
    id: 'llamaHtmlNode',
    label: 'HTML Node Parser (LlamaIndex)',
    description: 'Parses HTML elements into semantic nodes/chunks.',
  },
  {
    id: 'llamaSentence',
    label: 'Sentence Splitter (LlamaIndex)',
    description: 'Sentence-based splitting with configurable chunk size and overlap.',
    params: [
      { key: 'llamaSentenceSize', label: 'Chunk size', default: 1024, min: 200, max: 4000 },
      { key: 'llamaSentenceOverlap', label: 'Overlap', default: 20, min: 0, max: 400 },
    ],
  },
  {
    id: 'llamaSentenceWindow',
    label: 'Sentence Window Parser (LlamaIndex)',
    description: 'Builds sentence nodes with a configurable context window.',
    params: [{ key: 'llamaSentenceWindowSize', label: 'Window size', default: 3, min: 1, max: 10 }],
  },
  {
    id: 'llamaHierarchical',
    label: 'Hierarchical Node Parser (LlamaIndex)',
    description: 'Builds multi-level chunks and returns leaf-level nodes.',
    params: [
      { key: 'llamaHierarchicalLarge', label: 'Large chunk size', default: 512, min: 128, max: 4096 },
      { key: 'llamaHierarchicalMedium', label: 'Medium chunk size', default: 256, min: 64, max: 2048 },
      { key: 'llamaHierarchicalSmall', label: 'Small chunk size', default: 128, min: 32, max: 1024 },
    ],
  },
];
