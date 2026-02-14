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
];
