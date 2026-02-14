export interface Chunk {
  index: number;
  text: string;
  startOffset: number;
  endOffset: number;
}

export type ChunkingAlgorithmId =
  | 'character'
  | 'recursive'
  | 'token'
  | 'semantic'
  | 'clustering'
  | 'llm'
  | 'htmlHeader'
  | 'markdownHeader'
  | 'code'
  | 'recursiveJson'
  | 'llamaMarkdownElement'
  | 'llamaMarkdownNode'
  | 'llamaHtmlNode'
  | 'llamaSentence'
  | 'llamaSentenceWindow'
  | 'llamaHierarchical';

export interface ChunkingOption {
  id: ChunkingAlgorithmId;
  label: string;
  description: string;
  group: string;
  params?: { key: string; label: string; default: number; min?: number; max?: number }[];
}
