import type { Chunk } from '../types';

export function characterChunk(
  text: string,
  chunkSize: number = 500,
  chunkOverlap: number = 50
): Chunk[] {
  const chunks: Chunk[] = [];
  let start = 0;

  while (start < text.length) {
    const end = Math.min(start + chunkSize, text.length);
    chunks.push({
      index: chunks.length,
      text: text.slice(start, end),
      startOffset: start,
      endOffset: end,
    });
    start = end - (start + chunkSize >= text.length ? 0 : chunkOverlap);
  }

  return chunks;
}
