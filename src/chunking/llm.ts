import type { Chunk } from '../types';

// LLM-based chunking requires an API. For visualization we use paragraph-based
// splitting as a stand-in so users can still see "chunk" boundaries; the UI
// can note that real LLM chunking would use an API.
function splitParagraphs(text: string): { paragraph: string; start: number; end: number }[] {
  const result: { paragraph: string; start: number; end: number }[] = [];
  const blocks = text.split(/(\n\s*\n)/);
  let offset = 0;
  for (const block of blocks) {
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

export function llmChunk(text: string, maxChunkChars: number = 600): Chunk[] {
  const paragraphs = splitParagraphs(text);
  const chunks: Chunk[] = [];
  let chunkText = '';
  let chunkStart = 0;

  for (const { paragraph, start } of paragraphs) {
    const candidate = chunkText ? chunkText + '\n\n' + paragraph : paragraph;
    if (candidate.length >= maxChunkChars && chunkText.length > 0) {
      chunks.push({
        index: chunks.length,
        text: chunkText,
        startOffset: chunkStart,
        endOffset: start,
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
