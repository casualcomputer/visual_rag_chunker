import type { Chunk } from '../types';

// Approximate tokenization: ~4 chars per token for English (GPT-style heuristic).
function findTokenSplit(text: string, targetTokens: number, fromIndex: number): number {
  let count = 0;
  const words = text.slice(fromIndex).split(/(\s+)/);
  let pos = fromIndex;
  for (let i = 0; i < words.length; i += 2) {
    const word = words[i];
    const sep = words[i + 1] ?? '';
    const wordTokens = Math.ceil((word?.length ?? 0) / 4) + 1;
    const sepTokens = Math.ceil(sep.length / 4);
    if (count + wordTokens + sepTokens > targetTokens && count > 0) {
      return pos;
    }
    count += wordTokens + sepTokens;
    pos += (word?.length ?? 0) + sep.length;
  }
  return text.length;
}

export function tokenChunk(
  text: string,
  chunkSizeTokens: number = 256,
  chunkOverlapTokens: number = 25
): Chunk[] {
  const chunks: Chunk[] = [];
  let start = 0;

  while (start < text.length) {
    const end = findTokenSplit(text, chunkSizeTokens, start);
    const slice = text.slice(start, end);
    if (slice.length > 0) {
      chunks.push({
        index: chunks.length,
        text: slice,
        startOffset: start,
        endOffset: end,
      });
    }
    const overlapStart = Math.max(start, end - (chunkOverlapTokens * 4));
    start = overlapStart >= end ? end : overlapStart;
    if (start >= text.length) break;
  }

  return chunks;
}
