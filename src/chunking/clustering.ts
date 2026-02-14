import type { Chunk } from '../types';

// Clustering without embeddings: use paragraph/section boundaries as a proxy.
// Split by double newline (paragraphs), then optionally merge small paragraphs
// up to maxChunkChars. Represents "structure-based" clustering for demo.
function splitParagraphs(text: string): { paragraph: string; start: number; end: number }[] {
  const result: { paragraph: string; start: number; end: number }[] = [];
  const blocks = text.split(/(\n\s*\n)/);
  let offset = 0;
  for (let i = 0; i < blocks.length; i++) {
    const block = blocks[i];
    const trimmed = block.trim();
    if (trimmed.length > 0 && !/^\n\s*\n$/.test(block)) {
      result.push({
        paragraph: trimmed,
        start: offset,
        end: offset + block.length,
      });
    }
    offset += block.length;
  }
  if (result.length === 0 && text.trim().length > 0) {
    result.push({ paragraph: text.trim(), start: 0, end: text.length });
  }
  return result;
}

export function clusteringChunk(
  text: string,
  maxChunkChars: number = 1200
): Chunk[] {
  const paragraphs = splitParagraphs(text);
  const chunks: Chunk[] = [];
  let chunkText = '';
  let chunkStart = 0;

  for (const { paragraph, start } of paragraphs) {
    const candidate = chunkText ? chunkText + '\n\n' + paragraph : paragraph;
    if (candidate.length >= maxChunkChars && chunkText.length > 0) {
      const chunkEnd = start;
      chunks.push({
        index: chunks.length,
        text: chunkText,
        startOffset: chunkStart,
        endOffset: chunkEnd,
      });
      chunkText = paragraph;
      chunkStart = start;
    } else {
      chunkText = candidate || paragraph;
      if (chunkStart === 0 && chunkText) chunkStart = start;
    }
  }

  if (chunkText.length > 0) {
    const last = paragraphs[paragraphs.length - 1];
    chunks.push({
      index: chunks.length,
      text: chunkText,
      startOffset: chunkStart,
      endOffset: last ? last.end : text.length,
    });
  }

  return chunks;
}
