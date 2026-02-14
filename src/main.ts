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

function applyDocumentMode(): void {
  app.classList.toggle('doc-compact', isDocumentCompact);
  const toggleBtn = document.getElementById('toggle-document-size');
  if (toggleBtn) {
    toggleBtn.textContent = isDocumentCompact ? 'Expand document' : 'Compact document';
  }
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
  if (!currentText) {
    currentChunks = [];
    apiError = null;
    renderChunks();
    renderSourceHighlight();
    renderApiError();
    return;
  }
  apiError = null;
  renderApiError();
  const summaryEl = document.getElementById('chunk-summary');
  if (summaryEl) summaryEl.textContent = 'Chunking…';
  try {
    const reqParams: Record<string, number> = {};
    CHUNKING_OPTIONS.find((o) => o.id === currentAlgorithmId)?.params?.forEach((p) => {
      const v = params[p.key as keyof ChunkingParams];
      if (v !== undefined) reqParams[p.key] = v;
    });
    const res = await fetch(`${API_BASE}/chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: currentText,
        algorithm: currentAlgorithmId,
        params: reqParams,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    currentChunks = Array.isArray(data.chunks) ? data.chunks : [];
  } catch (e) {
    apiError = e instanceof Error ? e.message : 'Backend unavailable. Start the Python server (see README).';
    currentChunks = [];
  }
  renderChunks();
  renderSourceHighlight();
  if (activeChunkIndex !== null && currentChunks.some((c) => c.index === activeChunkIndex)) {
    highlightChunk(activeChunkIndex);
  }
  renderApiError();
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

function renderChunks(): void {
  const list = document.getElementById('chunk-list')!;
  list.innerHTML = '';
  currentChunks.forEach((chunk) => {
    const card = document.createElement('div');
    card.className = 'chunk-card';
    card.dataset.index = String(chunk.index);
    const title = document.createElement('div');
    title.className = 'chunk-title';
    title.textContent = `Chunk ${chunk.index + 1}`;
    const meta = document.createElement('div');
    meta.className = 'chunk-meta';
    meta.textContent = `${chunk.text.length} chars · #${chunk.index + 1}`;
    const body = document.createElement('pre');
    body.className = 'chunk-body';
    body.textContent = chunk.text.slice(0, 400) + (chunk.text.length > 400 ? '…' : '');
    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(body);
    card.addEventListener('click', () => highlightChunk(chunk.index));
    list.appendChild(card);
  });
  const summary = document.getElementById('chunk-summary')!;
  summary.textContent = currentChunks.length
    ? `${currentChunks.length} chunk${currentChunks.length === 1 ? '' : 's'}`
    : 'Load or upload a document and pick an algorithm.';
}

function highlightChunk(index: number): void {
  activeChunkIndex = index;
  document.querySelectorAll('.chunk-card').forEach((el) => el.classList.remove('active'));
  document.querySelector(`.chunk-card[data-index="${index}"]`)?.classList.add('active');
  const chunk = currentChunks.find((c) => c.index === index);
  if (!chunk) return;
  const source = document.getElementById('source-text')!;
  source.querySelectorAll('.source-segment').forEach((s) => {
    s.classList.remove('chunk-focus');
    for (let i = 0; i < 8; i += 1) s.classList.remove(`chunk-focus-${i}`);
  });
  const spans = source.querySelectorAll('.source-segment');
  spans.forEach((span) => {
    const start = parseInt(span.getAttribute('data-start') ?? '0', 10);
    const end = parseInt(span.getAttribute('data-end') ?? '0', 10);
    if (chunk.startOffset < end && chunk.endOffset > start) {
      span.classList.add('chunk-focus', `chunk-focus-${index % 8}`);
    }
  });
}

function renderSourceHighlight(): void {
  const container = document.getElementById('source-text')!;
  if (!currentText) {
    container.innerHTML = '<p class="placeholder">Upload a .md file or load the sample.</p>';
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
    }
    const startsHere = currentChunks.filter((c) => c.startOffset === seg.start).map((c) => c.index + 1);
    const endsHere = currentChunks.filter((c) => c.endOffset === seg.end).map((c) => c.index + 1);
    if (startsHere.length) {
      span.classList.add('boundary-start');
      span.title = `Start: ${startsHere.map((i) => `#${i}`).join(', ')}`;
    }
    if (endsHere.length) {
      span.classList.add('boundary-end');
      const endText = `End: ${endsHere.map((i) => `#${i}`).join(', ')}`;
      span.title = span.title ? `${span.title} | ${endText}` : endText;
    }
    span.textContent = currentText.slice(seg.start, seg.end);
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
          <input type="file" id="file-input" accept=".md,text/markdown,text/plain" hidden />
          Upload .md
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
        <div id="source-text" class="source-text"><p class="placeholder">Upload a .md file or load the sample.</p></div>
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

  CHUNKING_OPTIONS.forEach((opt) => {
    const option = document.createElement('option');
    option.value = opt.id;
    option.textContent = opt.label;
    if (opt.id === currentAlgorithmId) option.selected = true;
    algorithmSelect.appendChild(option);
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
