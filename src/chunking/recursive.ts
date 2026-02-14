import type { Chunk } from '../types';

const DEFAULT_SEPARATORS = ['\n\n', '\n', '. ', '? ', '! ', '; ', ', ', ' ', ''];

export function recursiveCharacterChunk(
  text: string,
  chunkSize: number = 500,
  chunkOverlap: number = 50,
  separators: string[] = DEFAULT_SEPARATORS
): Chunk[] {
  const chunks: Chunk[] = [];

  function splitAt(s: string, startOffset: number): void {
    if (s.length <= chunkSize) {
      if (s.length > 0) {
        chunks.push({
          index: chunks.length,
          text: s,
          startOffset,
          endOffset: startOffset + s.length,
        });
      }
      return;
    }

    let splitIdx = -1;

    for (const sep of separators) {
      const idx = s.slice(0, chunkSize).lastIndexOf(sep);
      if (idx > 0) {
        splitIdx = idx + sep.length;
        break;
      }
    }

    if (splitIdx <= 0) {
      splitIdx = Math.min(chunkSize, s.length);
    }

    const head = s.slice(0, splitIdx);
    const tail = s.slice(splitIdx);

    if (head.length > 0) {
      chunks.push({
        index: chunks.length,
        text: head,
        startOffset,
        endOffset: startOffset + head.length,
      });
    }

    const overlapStart = Math.max(0, splitIdx - chunkOverlap);
    const overlapText = s.slice(overlapStart, splitIdx);
    const tailWithOverlap = overlapText + tail;

    if (tailWithOverlap.length > 0) {
      splitAt(tailWithOverlap, startOffset + splitIdx - overlapText.length);
    }
  }

  splitAt(text, 0);
  return chunks;
}
