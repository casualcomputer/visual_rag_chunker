import type { Chunk } from '../types';

// Sentence-boundary chunking without embeddings: split on sentences, then group
// consecutive sentences up to maxChunkChars. Mimics "semantic" structure by
// respecting sentence boundaries (as in the LanceDB blog's first step).
function splitSentences(text: string): { sentence: string; start: number; end: number }[] {
  const result: { sentence: string; start: number; end: number }[] = [];
  // Match sentence endings: . ! ? followed by space or end, but not abbreviations like "e.g."
  const re = /[^.!?]*[.!?]+[\s]*/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const s = m[0].trim();
    if (s.length > 0) {
      result.push({
        sentence: s,
        start: m.index,
        end: m.index + m[0].length,
      });
    }
  }
  const last = result.length ? result[result.length - 1].end : 0;
  if (last < text.length) {
    const tail = text.slice(last).trim();
    if (tail.length > 0) {
      result.push({ sentence: tail, start: last, end: text.length });
    }
  }
  return result;
}

export function semanticChunk(
  text: string,
  maxChunkChars: number = 800,
  minChunkChars: number = 100
): Chunk[] {
  const sentences = splitSentences(text);
  const chunks: Chunk[] = [];
  let chunkText = '';
  let chunkStartOffset = 0;

  for (const { sentence, start } of sentences) {
    const candidate = chunkText ? chunkText + ' ' + sentence : sentence;
    if (candidate.length >= maxChunkChars && chunkText.length >= minChunkChars) {
      chunks.push({
        index: chunks.length,
        text: chunkText,
        startOffset: chunkStartOffset,
        endOffset: start,
      });
      chunkText = sentence;
      chunkStartOffset = start;
    } else {
      chunkText = candidate || sentence;
      if (!chunkText) chunkStartOffset = start;
    }
  }

  if (chunkText.length > 0) {
    const lastSentence = sentences[sentences.length - 1];
    chunks.push({
      index: chunks.length,
      text: chunkText,
      startOffset: chunkStartOffset,
      endOffset: lastSentence ? lastSentence.end : text.length,
    });
  }

  return chunks;
}
