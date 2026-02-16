import './style.css';
import type { Chunk } from './types';
import type { ChunkingParams } from './chunking';
import { CHUNKING_OPTIONS } from './options';
import sampleMd from '../data/sample.md?raw';

const API_BASE = (typeof import.meta !== 'undefined' && (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL) || 'http://localhost:8000';

const app = document.getElementById('app')!;

let currentText = '';
let currentChunks: Chunk[] = [];
let currentAlgorithmId = 'recursive';
let activeChunkIndex: number | null = null;
let isDocumentCompact = true;
const params: ChunkingParams = {};
let apiError: string | null = null;
let apiWarning: string | null = null;
let chunkRequestSeq = 0;
let inFlightChunkRequest: AbortController | null = null;

function applyDocumentMode(): void {
  app.classList.toggle('doc-compact', isDocumentCompact);
  const toggleBtn = document.getElementById('toggle-document-size');
  if (toggleBtn) {
    toggleBtn.textContent = isDocumentCompact ? 'Expand document' : 'Compact document';
  }
}

function setChunkingState(loading: boolean): void {
  app.classList.toggle('is-loading', loading);

  const summary = document.getElementById('chunk-summary');
  if (summary) {
    summary.classList.toggle('loading', loading);
    if (loading) summary.textContent = 'Chunking…';
  }

  const algorithm = document.getElementById('algorithm') as HTMLSelectElement | null;
  if (algorithm) algorithm.disabled = loading;

  const fileInput = document.getElementById('file-input') as HTMLInputElement | null;
  if (fileInput) fileInput.disabled = loading;

  const loadSampleBtn = document.getElementById('load-sample') as HTMLButtonElement | null;
  if (loadSampleBtn) loadSampleBtn.disabled = loading;

  const toggleSizeBtn = document.getElementById('toggle-document-size') as HTMLButtonElement | null;
  if (toggleSizeBtn) toggleSizeBtn.disabled = loading;

  document.querySelectorAll('#params input').forEach((el) => {
    (el as HTMLInputElement).disabled = loading;
  });
}

function getDefaultParams(algorithmId: string): Record<string, number> {
  const opt = CHUNKING_OPTIONS.find((o) => o.id === algorithmId);
  const out: Record<string, number> = {};
  opt?.params?.forEach((p) => (out[p.key] = p.default));
  return out;
}

function renderParamInputs(algorithmId: string): void {
  const opt = CHUNKING_OPTIONS.find((o) => o.id === algorithmId);
  const container = document.getElementById('params')!;
  container.innerHTML = '';
  if (!opt?.params?.length) return;
  opt.params.forEach((p) => {
    const label = document.createElement('label');
    label.textContent = p.label + ': ';
    const input = document.createElement('input');
    input.type = 'number';
    input.id = 'param-' + p.key;
    input.value = String(params[p.key as keyof ChunkingParams] ?? p.default);
    input.min = String(p.min ?? 0);
    input.max = String(p.max ?? 10000);
    input.addEventListener('change', () => {
      const v = parseInt(input.value, 10);
      if (!isNaN(v)) (params as Record<string, number>)[p.key] = v;
      updateChunks();
    });
    label.appendChild(input);
    container.appendChild(label);
  });
}

async function updateChunks(): Promise<void> {
  const requestSeq = ++chunkRequestSeq;

  inFlightChunkRequest?.abort();
  const controller = new AbortController();
  inFlightChunkRequest = controller;

  if (!currentText) {
    setChunkingState(false);
    currentChunks = [];
    apiError = null;
    apiWarning = null;
    renderChunks();
    renderSourceHighlight();
    renderApiError();
    renderApiWarning();
    return;
  }
  setChunkingState(true);
  apiError = null;
  apiWarning = null;
  renderApiError();
  renderApiWarning();
  try {
    const reqParams: Record<string, number> = {};
    CHUNKING_OPTIONS.find((o) => o.id === currentAlgorithmId)?.params?.forEach((p) => {
      const v = params[p.key as keyof ChunkingParams];
      if (v !== undefined) reqParams[p.key] = v;
    });
    const res = await fetch(`${API_BASE}/chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        text: currentText,
        algorithm: currentAlgorithmId,
        params: reqParams,
      }),
    });
    if (requestSeq !== chunkRequestSeq) return;
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    if (requestSeq !== chunkRequestSeq) return;
    currentChunks = Array.isArray(data.chunks) ? data.chunks : [];
    apiWarning = typeof data.warning === 'string' && data.warning.trim() ? data.warning : null;
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') return;
    if (requestSeq !== chunkRequestSeq) return;
    apiError = e instanceof Error ? e.message : 'Backend unavailable. Start the Python server (see README).';
    apiWarning = null;
    currentChunks = [];
  } finally {
    if (requestSeq === chunkRequestSeq && inFlightChunkRequest === controller) {
      inFlightChunkRequest = null;
    }
    if (requestSeq === chunkRequestSeq) {
      setChunkingState(false);
    }
  }
  renderChunks();
  renderSourceHighlight();
  if (activeChunkIndex !== null && currentChunks.some((c) => c.index === activeChunkIndex)) {
    highlightChunk(activeChunkIndex);
  }
  renderApiError();
  renderApiWarning();
}

function renderApiError(): void {
  let banner = document.getElementById('api-error-banner');
  if (apiError) {
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'api-error-banner';
      banner.className = 'api-error-banner';
      app.querySelector('.controls')?.after(banner);
    }
    banner.textContent = apiError;
    banner.classList.add('visible');
  } else if (banner) {
    banner.classList.remove('visible');
      banner.textContent = '';
  }
}

function renderApiWarning(): void {
  let banner = document.getElementById('api-warning-banner');
  if (apiWarning) {
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'api-warning-banner';
      banner.className = 'api-warning-banner';
      app.querySelector('.controls')?.after(banner);
    }
    banner.textContent = apiWarning;
    banner.classList.add('visible');
  } else if (banner) {
    banner.classList.remove('visible');
    banner.textContent = '';
  }
}

function renderChunks(): void {
  const list = document.getElementById('chunk-list')!;
  list.innerHTML = '';
  currentChunks.forEach((chunk, idx) => {
    const card = document.createElement('div');
    card.className = `chunk-card chunk-card-color-${chunk.index % 8}`;
    card.dataset.index = String(chunk.index);
    const title = document.createElement('div');
    title.className = 'chunk-title';
    title.textContent = `Chunk ${chunk.index + 1}`;
    const meta = document.createElement('div');
    meta.className = 'chunk-meta';
    const next = currentChunks[idx + 1];
    const overlapWithNext = next ? Math.max(0, chunk.endOffset - next.startOffset) : 0;
    const overlapNote = overlapWithNext > 0 ? ` · overlaps next by ${overlapWithNext} chars` : '';
    meta.textContent = `${chunk.text.length} chars · offset ${chunk.startOffset}–${chunk.endOffset}${overlapNote}`;
    const body = document.createElement('pre');
    body.className = 'chunk-body';
    let previewText = chunk.text;
    if (chunk.text.length > 400) {
      const head = chunk.text.slice(0, 220);
      const tail = chunk.text.slice(-140);
      const omitted = chunk.text.length - head.length - tail.length;
      previewText = `${head}\n\n... [${omitted} chars omitted in middle] ...\n\n${tail}`;
    }
    body.textContent = `[[UI preview: chunk start]]\n${previewText}\n[[UI preview: chunk end]]`;
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(body);
    card.addEventListener('click', () => highlightChunk(chunk.index));
    list.appendChild(card);
  });
  const summary = document.getElementById('chunk-summary')!;
  if (currentChunks.length && currentText) {
    const coveredChars = new Set<number>();
    currentChunks.forEach((c) => {
      for (let i = c.startOffset; i < c.endOffset; i++) coveredChars.add(i);
    });
    const nonWhitespaceTotal = [...currentText].reduce((n, ch) => n + (ch.trim() ? 1 : 0), 0);
    let nonWhitespaceCovered = 0;
    for (let i = 0; i < currentText.length; i++) {
      if (currentText[i].trim() && coveredChars.has(i)) nonWhitespaceCovered++;
    }
    const pct = nonWhitespaceTotal > 0 ? Math.round((nonWhitespaceCovered / nonWhitespaceTotal) * 100) : 100;
    const coverageNote = pct < 100 ? ` · ${pct}% covered` : '';
    summary.textContent = `${currentChunks.length} chunk${currentChunks.length === 1 ? '' : 's'}${coverageNote}`;
  } else {
    summary.textContent = 'Load or upload a document and pick an algorithm.';
  }
}

function highlightChunk(index: number): void {
  activeChunkIndex = index;
  document.querySelectorAll('.chunk-card').forEach((el) => el.classList.remove('active'));
  const activeCard = document.querySelector(`.chunk-card[data-index="${index}"]`);
  activeCard?.classList.add('active');
  const chunk = currentChunks.find((c) => c.index === index);
  if (!chunk) return;
  const source = document.getElementById('source-text')!;
  source.querySelectorAll('.source-segment').forEach((s) => {
    s.classList.remove('chunk-focus');
    for (let i = 0; i < 8; i += 1) s.classList.remove(`chunk-focus-${i}`);
  });
  let firstFocused: Element | null = null;
  const spans = source.querySelectorAll('.source-segment');
  spans.forEach((span) => {
    const start = parseInt(span.getAttribute('data-start') ?? '0', 10);
    const end = parseInt(span.getAttribute('data-end') ?? '0', 10);
    if (chunk.startOffset < end && chunk.endOffset > start) {
      span.classList.add('chunk-focus', `chunk-focus-${index % 8}`);
      if (!firstFocused) firstFocused = span;
    }
  });
  // Scroll document to show highlighted region
  if (firstFocused) {
    (firstFocused as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
  // Scroll chunk card into view in sidebar
  if (activeCard) {
    (activeCard as HTMLElement).scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function renderSourceHighlight(): void {
  const container = document.getElementById('source-text')!;
  if (!currentText) {
    container.innerHTML = '<p class="placeholder">Upload a document (.md/.html) or load the sample.</p>';
    return;
  }
  container.innerHTML = '';
  if (currentChunks.length === 0) {
    const pre = document.createElement('pre');
    pre.className = 'source-raw';
    pre.textContent = currentText;
    container.appendChild(pre);
    return;
  }
  const boundaries = new Set<number>([0, currentText.length]);
  currentChunks.forEach((c) => {
    boundaries.add(Math.max(0, Math.min(currentText.length, c.startOffset)));
    boundaries.add(Math.max(0, Math.min(currentText.length, c.endOffset)));
  });
  const sortedBoundaries = [...boundaries].sort((a, b) => a - b);
  const segments: { start: number; end: number }[] = [];
  for (let i = 0; i < sortedBoundaries.length - 1; i += 1) {
    const start = sortedBoundaries[i];
    const end = sortedBoundaries[i + 1];
    if (end > start) segments.push({ start, end });
  }
  segments.forEach((seg) => {
    const span = document.createElement('span');
    span.className = 'source-segment';
    span.setAttribute('data-start', String(seg.start));
    span.setAttribute('data-end', String(seg.end));
    const covering = currentChunks
      .filter((c) => c.startOffset < seg.end && c.endOffset > seg.start)
      .map((c) => c.index)
      .sort((a, b) => a - b);
    if (covering.length > 0) {
      const baseChunkIndex = covering[0];
      span.classList.add(`chunk-bg-${baseChunkIndex % 8}`);
      span.setAttribute('data-chunks', covering.map((i) => `#${i + 1}`).join(', '));
    } else {
      // Mark uncovered text so users can see gaps
      const segText = currentText.slice(seg.start, seg.end);
      if (segText.trim().length > 0) {
        span.classList.add('source-uncovered');
        span.setAttribute('data-tooltip', 'Not covered by any chunk');
      }
    }
    const startsHere = currentChunks.filter((c) => c.startOffset === seg.start).map((c) => c.index + 1);
    const endsHere = currentChunks.filter((c) => c.endOffset === seg.end).map((c) => c.index + 1);
    if (startsHere.length) {
      span.classList.add('boundary-start');
    }
    if (endsHere.length) {
      span.classList.add('boundary-end');
    }
    // Build rich tooltip info
    if (covering.length > 0) {
      const parts: string[] = [];
      parts.push(covering.length === 1 ? `Chunk #${covering[0] + 1}` : `Chunks ${covering.map((i) => `#${i + 1}`).join(', ')}`);
      if (covering.length > 1) parts.push('(overlap)');
      if (startsHere.length) parts.push(`| Start: ${startsHere.map((i) => `#${i}`).join(', ')}`);
      if (endsHere.length) parts.push(`| End: ${endsHere.map((i) => `#${i}`).join(', ')}`);
      span.setAttribute('data-tooltip', parts.join(' '));
    }
    span.textContent = currentText.slice(seg.start, seg.end);

    // Bidirectional: hover on document highlights chunk card
    if (covering.length > 0) {
      span.style.cursor = 'pointer';
      span.addEventListener('mouseenter', () => {
        covering.forEach((ci) => {
          document.querySelector(`.chunk-card[data-index="${ci}"]`)?.classList.add('hovered');
        });
      });
      span.addEventListener('mouseleave', () => {
        document.querySelectorAll('.chunk-card.hovered').forEach((el) => el.classList.remove('hovered'));
      });
      // Click on document text selects the first covering chunk
      span.addEventListener('click', () => {
        highlightChunk(covering[0]);
      });
    }

    container.appendChild(span);
  });
}

function setText(text: string): void {
  currentText = text;
  activeChunkIndex = null;
  updateChunks();
}

function init(): void {
  app.innerHTML = `
    <header class="header">
      <h1>Chunking Visualization</h1>
      <p class="subtitle">Compare chunking strategies from the <a href="https://lancedb.com/blog/chunking-analysis-which-is-the-right-chunking-approach-for-your-language/" target="_blank" rel="noopener">LanceDB chunking analysis</a></p>
    </header>
    <div class="controls">
      <div class="upload-row">
        <label class="btn btn-primary">
          <input type="file" id="file-input" accept=".md,.html,.htm,text/markdown,text/plain,text/html" hidden />
          Upload document (.md/.html)
        </label>
        <button type="button" id="load-sample" class="btn btn-secondary">Load sample</button>
      </div>
      <div class="algorithm-row">
        <label for="algorithm">Algorithm</label>
        <select id="algorithm" name="algorithm"></select>
        <div id="params" class="params"></div>
      </div>
    </div>
    <div class="layout">
      <aside class="chunks-panel">
        <h2>Chunks</h2>
        <p id="chunk-summary" class="chunk-summary">Load or upload a document.</p>
        <div id="chunk-list" class="chunk-list"></div>
      </aside>
      <main class="source-panel">
        <div class="panel-head">
          <h2>Document</h2>
          <button type="button" id="toggle-document-size" class="btn btn-ghost">Expand document</button>
        </div>
        <div id="source-text" class="source-text"><p class="placeholder">Upload a document (.md/.html) or load the sample.</p></div>
      </main>
    </div>
  `;

  const fileInput = document.getElementById('file-input') as HTMLInputElement;
  const loadSample = document.getElementById('load-sample')!;
  const algorithmSelect = document.getElementById('algorithm') as HTMLSelectElement;
  const toggleDocumentSize = document.getElementById('toggle-document-size') as HTMLButtonElement;

  fileInput.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setText(String(reader.result ?? ''));
    reader.readAsText(file);
  });

  loadSample.addEventListener('click', () => setText(sampleMd));

  const groups = new Map<string, typeof CHUNKING_OPTIONS>();
  CHUNKING_OPTIONS.forEach((opt) => {
    const g = opt.group ?? 'Other';
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g)!.push(opt);
  });
  groups.forEach((opts, groupName) => {
    const optgroup = document.createElement('optgroup');
    optgroup.label = groupName;
    opts.forEach((opt) => {
      const option = document.createElement('option');
      option.value = opt.id;
      option.textContent = opt.label;
      if (opt.id === currentAlgorithmId) option.selected = true;
      optgroup.appendChild(option);
    });
    algorithmSelect.appendChild(optgroup);
  });

  algorithmSelect.addEventListener('change', () => {
    currentAlgorithmId = algorithmSelect.value;
    activeChunkIndex = null;
    Object.assign(params, getDefaultParams(currentAlgorithmId));
    renderParamInputs(currentAlgorithmId);
    updateChunks();
  });

  toggleDocumentSize.addEventListener('click', () => {
    isDocumentCompact = !isDocumentCompact;
    applyDocumentMode();
  });

  renderParamInputs(currentAlgorithmId);
  Object.assign(params, getDefaultParams(currentAlgorithmId));
  applyDocumentMode();
}

init();
