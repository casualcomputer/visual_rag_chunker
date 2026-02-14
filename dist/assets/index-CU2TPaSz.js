(function(){const s=document.createElement("link").relList;if(s&&s.supports&&s.supports("modulepreload"))return;for(const e of document.querySelectorAll('link[rel="modulepreload"]'))r(e);new MutationObserver(e=>{for(const t of e)if(t.type==="childList")for(const a of t.addedNodes)a.tagName==="LINK"&&a.rel==="modulepreload"&&r(a)}).observe(document,{childList:!0,subtree:!0});function i(e){const t={};return e.integrity&&(t.integrity=e.integrity),e.referrerPolicy&&(t.referrerPolicy=e.referrerPolicy),e.crossOrigin==="use-credentials"?t.credentials="include":e.crossOrigin==="anonymous"?t.credentials="omit":t.credentials="same-origin",t}function r(e){if(e.ep)return;e.ep=!0;const t=i(e);fetch(e.href,t)}})();const y=[{id:"character",label:"CharacterTextSplitter",description:"Splits by a fixed number of characters.",params:[{key:"characterSize",label:"Chunk size",default:500,min:100,max:2e3},{key:"characterOverlap",label:"Overlap",default:50,min:0,max:200}]},{id:"recursive",label:"RecursiveCharacterTextSplitter",description:"Splits on paragraphs, then lines, then sentences, then words.",params:[{key:"recursiveSize",label:"Chunk size",default:500,min:100,max:2e3},{key:"recursiveOverlap",label:"Overlap",default:50,min:0,max:200}]},{id:"token",label:"TokenTextSplitter",description:"Splits by approximate token count (word-based heuristic).",params:[{key:"tokenSize",label:"Tokens per chunk",default:256,min:50,max:512},{key:"tokenOverlap",label:"Overlap (tokens)",default:25,min:0,max:100}]},{id:"semantic",label:"Semantic Chunking",description:"NLTK sentences + cosine similarity threshold (sequential semantic).",params:[{key:"semanticMax",label:"Max chunk chars",default:800,min:200,max:2e3},{key:"semanticMin",label:"Min chunk chars",default:100,min:50,max:500},{key:"semanticPercentile",label:"Similarity threshold percentile",default:90,min:70,max:99}]},{id:"clustering",label:"Clustering (CRAG-style)",description:"Sentence embeddings + K-means clustering.",params:[{key:"clusteringMax",label:"Max chunk chars",default:1200,min:300,max:3e3},{key:"clusteringMin",label:"Min chunk chars",default:100,min:50,max:500}]},{id:"llm",label:"LLM-based (Agent assisted)",description:"Paragraph-based proxy; real implementation would use an LLM API.",params:[{key:"llmMax",label:"Max chunk chars",default:600,min:200,max:1500}]}],w=`# Chunking Analysis Sample

This is a sample markdown document for testing chunking strategies. Chunking refers to breaking down longer texts into smaller pieces for retrieval systems.

## Why Chunking Matters

When building RAG applications, you need to split documents into chunks before creating embeddings. The choice of chunking strategy affects retrieval quality.

Different approaches exist: fixed character splitting, semantic chunking, and clustering-based methods. Each has trade-offs between context preservation and granularity.

## Common Strategies

**CharacterTextSplitter** splits by a fixed number of characters. Simple but can break words or sentences mid-way.

**RecursiveCharacterTextSplitter** tries to split on natural boundaries first: paragraphs, then lines, then sentences, then words. It respects structure better.

**TokenTextSplitter** splits by token count, which aligns with how language models see text. Token limits matter for API calls.

**Semantic Chunking** groups text by meaning using embeddings. Consecutive sentences with similar meaning form one chunk. Better for retrieval but needs an embedding model.

**Clustering (CRAG)** splits into sentences, embeds them, then clusters by similarity. Topics end up together even if they appear in different parts of the document.

**LLM-based chunking** uses a language model to create propositions or to split the document. Highest quality but requires API calls and cost.

## Summary

No single strategy fits all use cases. Try several on your documents and measure retrieval quality for your queries.
`,b={},O=typeof import.meta<"u"&&(b==null?void 0:b.VITE_API_URL)||"http://localhost:8000",x=document.getElementById("app");let d="",o=[],u="recursive",m=null,g=!0;const f={};let p=null;function E(){x.classList.toggle("doc-compact",g);const n=document.getElementById("toggle-document-size");n&&(n.textContent=g?"Expand document":"Compact document")}function S(n){var r;const s=y.find(e=>e.id===n),i={};return(r=s==null?void 0:s.params)==null||r.forEach(e=>i[e.key]=e.default),i}function L(n){var r;const s=y.find(e=>e.id===n),i=document.getElementById("params");i.innerHTML="",(r=s==null?void 0:s.params)!=null&&r.length&&s.params.forEach(e=>{const t=document.createElement("label");t.textContent=e.label+": ";const a=document.createElement("input");a.type="number",a.id="param-"+e.key,a.value=String(f[e.key]??e.default),a.min=String(e.min??0),a.max=String(e.max??1e4),a.addEventListener("change",()=>{const c=parseInt(a.value,10);isNaN(c)||(f[e.key]=c),v()}),t.appendChild(a),i.appendChild(t)})}async function v(){var s,i;if(!d){o=[],p=null,I(),T(),k();return}p=null,k();const n=document.getElementById("chunk-summary");n&&(n.textContent="Chunking…");try{const r={};(i=(s=y.find(a=>a.id===u))==null?void 0:s.params)==null||i.forEach(a=>{const c=f[a.key];c!==void 0&&(r[a.key]=c)});const e=await fetch(`${O}/chunk`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:d,algorithm:u,params:r})});if(!e.ok){const a=await e.json().catch(()=>({detail:e.statusText}));throw new Error(a.detail||e.statusText)}const t=await e.json();o=Array.isArray(t.chunks)?t.chunks:[]}catch(r){p=r instanceof Error?r.message:"Backend unavailable. Start the Python server (see README).",o=[]}I(),T(),m!==null&&o.some(r=>r.index===m)&&M(m),k()}function k(){var s;let n=document.getElementById("api-error-banner");p?(n||(n=document.createElement("div"),n.id="api-error-banner",n.className="api-error-banner",(s=x.querySelector(".controls"))==null||s.after(n)),n.textContent=p,n.classList.add("visible")):n&&(n.classList.remove("visible"),n.textContent="")}function I(){const n=document.getElementById("chunk-list");n.innerHTML="",o.forEach(i=>{const r=document.createElement("div");r.className="chunk-card",r.dataset.index=String(i.index);const e=document.createElement("div");e.className="chunk-title",e.textContent=`Chunk ${i.index+1}`;const t=document.createElement("div");t.className="chunk-meta",t.textContent=`${i.text.length} chars · #${i.index+1}`;const a=document.createElement("pre");a.className="chunk-body",a.textContent=i.text.slice(0,400)+(i.text.length>400?"…":""),r.appendChild(e),r.appendChild(t),r.appendChild(a),r.addEventListener("click",()=>M(i.index)),n.appendChild(r)});const s=document.getElementById("chunk-summary");s.textContent=o.length?`${o.length} chunk${o.length===1?"":"s"}`:"Load or upload a document and pick an algorithm."}function M(n){var e;m=n,document.querySelectorAll(".chunk-card").forEach(t=>t.classList.remove("active")),(e=document.querySelector(`.chunk-card[data-index="${n}"]`))==null||e.classList.add("active");const s=o.find(t=>t.index===n);if(!s)return;const i=document.getElementById("source-text");i.querySelectorAll(".source-segment").forEach(t=>{t.classList.remove("chunk-focus");for(let a=0;a<8;a+=1)t.classList.remove(`chunk-focus-${a}`)}),i.querySelectorAll(".source-segment").forEach(t=>{const a=parseInt(t.getAttribute("data-start")??"0",10),c=parseInt(t.getAttribute("data-end")??"0",10);s.startOffset<c&&s.endOffset>a&&t.classList.add("chunk-focus",`chunk-focus-${n%8}`)})}function T(){const n=document.getElementById("source-text");if(!d){n.innerHTML='<p class="placeholder">Upload a .md file or load the sample.</p>';return}if(n.innerHTML="",o.length===0){const e=document.createElement("pre");e.className="source-raw",e.textContent=d,n.appendChild(e);return}const s=new Set([0,d.length]);o.forEach(e=>{s.add(Math.max(0,Math.min(d.length,e.startOffset))),s.add(Math.max(0,Math.min(d.length,e.endOffset)))});const i=[...s].sort((e,t)=>e-t),r=[];for(let e=0;e<i.length-1;e+=1){const t=i[e],a=i[e+1];a>t&&r.push({start:t,end:a})}r.forEach(e=>{const t=document.createElement("span");t.className="source-segment",t.setAttribute("data-start",String(e.start)),t.setAttribute("data-end",String(e.end));const a=o.filter(l=>l.startOffset<e.end&&l.endOffset>e.start).map(l=>l.index).sort((l,h)=>l-h);if(a.length>0){const l=a[0];t.classList.add(`chunk-bg-${l%8}`),t.setAttribute("data-chunks",a.map(h=>`#${h+1}`).join(", "))}const c=o.filter(l=>l.startOffset===e.start).map(l=>l.index+1),C=o.filter(l=>l.endOffset===e.end).map(l=>l.index+1);if(c.length&&(t.classList.add("boundary-start"),t.title=`Start: ${c.map(l=>`#${l}`).join(", ")}`),C.length){t.classList.add("boundary-end");const l=`End: ${C.map(h=>`#${h}`).join(", ")}`;t.title=t.title?`${t.title} | ${l}`:l}t.textContent=d.slice(e.start,e.end),n.appendChild(t)})}function A(n){d=n,m=null,v()}function B(){x.innerHTML=`
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
  `;const n=document.getElementById("file-input"),s=document.getElementById("load-sample"),i=document.getElementById("algorithm"),r=document.getElementById("toggle-document-size");n.addEventListener("change",()=>{var a;const e=(a=n.files)==null?void 0:a[0];if(!e)return;const t=new FileReader;t.onload=()=>A(String(t.result??"")),t.readAsText(e)}),s.addEventListener("click",()=>A(w)),y.forEach(e=>{const t=document.createElement("option");t.value=e.id,t.textContent=e.label,e.id===u&&(t.selected=!0),i.appendChild(t)}),i.addEventListener("change",()=>{u=i.value,m=null,Object.assign(f,S(u)),L(u),v()}),r.addEventListener("click",()=>{g=!g,E()}),L(u),Object.assign(f,S(u)),E()}B();
