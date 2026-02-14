/**
 * Chunking is performed by the Python backend (LanceDB blog algorithms).
 * This module only exports the params type for the UI.
 */
export type ChunkingParams = {
  characterSize?: number;
  characterOverlap?: number;
  recursiveSize?: number;
  recursiveOverlap?: number;
  tokenSize?: number;
  tokenOverlap?: number;
  semanticMax?: number;
  semanticMin?: number;
  semanticPercentile?: number;
  clusteringMax?: number;
  clusteringMin?: number;
  numClusters?: number;
  llmMax?: number;
  codeChunkSize?: number;
  codeChunkOverlap?: number;
  jsonMaxChunkSize?: number;
  llamaSentenceSize?: number;
  llamaSentenceOverlap?: number;
  llamaSentenceWindowSize?: number;
  llamaHierarchicalLarge?: number;
  llamaHierarchicalMedium?: number;
  llamaHierarchicalSmall?: number;
};
