// ===============================
// Monaco boot
// ===============================
let editor, model;
require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@0.45.0/min/vs' } });

require(['vs/editor/editor.main'], function () {
  const sample = `// Bienvenido a Compiscript IDE
let x: integer = 2;
function add(a: integer, b: integer): integer { return a + b; }
let z: integer = add(1, 2);

// Prueba un error:
// if (x) { }  // <- cond no booleana
`;

  editor = monaco.editor.create(document.getElementById('editor'), {
    value: sample,
    language: 'typescript',    // highlight aproximado (cosmético)
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 14,
    roundedSelection: true,
    scrollBeyondLastLine: false
  });

  model = editor.getModel();

  // Atajo Ctrl/Cmd+Enter
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, analyze);

  // UI wires
  wireUI();
  // Theme inicial y texto del botón
  const initialTheme = localStorage.getItem('theme') || 'light';
  setTheme(initialTheme);
  updateThemeButtonText(initialTheme);
});

// ===============================
// Helpers DOM
// ===============================
function $(id) { return document.getElementById(id); }

// ===============================
// UI & Behavior
// ===============================
function wireUI() {
  $('analyze')?.addEventListener('click', analyze);
  const uploadBtn   = $('uploadBtn');
  const uploadInput = $('uploadInput');
  const filenameEl  = $('filename');

  uploadBtn?.addEventListener('click', () => uploadInput?.click());
  uploadInput?.addEventListener('change', async (ev) => {
    const file = ev.target.files && ev.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      setStatus('Subiendo…');
      const res = await fetch('/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (!data.ok) {
        toast('Error al subir archivo', 'err');
        return;
      }
      editor.setValue(data.code || '');
      filenameEl.textContent = data.filename ? '(' + data.filename + ')' : '';
      toast('Archivo cargado', 'ok');
    } catch (e) {
      toast('Fallo al subir: ' + String(e), 'err');
    } finally {
      uploadInput.value = '';
      setStatus('Listo');
    }
  });

  // Tabs (Errores / Símbolos)
  for (const el of document.querySelectorAll('.tab')) {
    el.addEventListener('click', () => activateTab(el.dataset.tab));
  }

  // Tema con texto dinámico
  $('themeToggle')?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    setTheme(next);
    updateThemeButtonText(next);
  });

  // Splitter
  initSplitter();
}

function activateTab(name) {
  for (const t of document.querySelectorAll('.tab')) {
    t.classList.toggle('active', t.dataset.tab === name);
  }
  $('errors').style.display = (name === 'errors') ? 'block' : 'none';
  $('symbols').style.display = (name === 'symbols') ? 'block' : 'none';
}

function setTheme(mode) {
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  monaco.editor.setTheme(mode === 'dark' ? 'vs-dark' : 'vs');
}

function updateThemeButtonText(mode) {
  // Mostrar el nombre del modo actual en el botón (Claro/Oscuro)
  const btn = $('themeToggle');
  if (!btn) return;
  btn.textContent = (mode === 'dark') ? '☀️ Claro' : '🌑 Oscuro';
}

function setStatus(text, type='') {
  const chip = $('statusChip');
  chip.textContent = text;
  chip.classList.remove('ok','err','warn');
  if (type) chip.classList.add(type);
}

function toast(text, kind='ok') {
  setStatus(text, kind);
  setTimeout(() => setStatus('Listo'), 1200);
}

// ===============================
// Analyze flow
// ===============================
async function analyze() {
  const source = editor.getValue();

  setStatus('Analizando…');
  let res;
  try {
    const r = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source })
    });
    res = await r.json();
  } catch (e) {
    res = { ok:false, errors:[{ code:'NET', message:String(e), line:1, column:1 }], symbols: null };
  }

  // Limpiar markers
  monaco.editor.setModelMarkers(model, 'compiscript', []);

  const panel = $('errors');
  panel.innerHTML = '';

  if (res.ok) {
    panel.innerHTML = `<div class="msg-ok">✔ Sin errores</div>`;
  } else {
    // Mostrar lista y markers
    const markers = [];
    for (const err of (res.errors || [])) {
      const l = Number(err.line) || 1;
      const c = Number(err.column) || 1;
      const code = err.code || 'ERR';
      const msg  = err.message || 'Error';

      const div = document.createElement('div');
      div.className = 'err';
      div.textContent = `[${code}] (${l}:${c}) ${msg}`;
      div.onclick = () => {
        editor.revealLineInCenter(l);
        editor.setPosition({ lineNumber: l, column: c });
        editor.focus();
      };
      panel.appendChild(div);

      markers.push({
        severity: monaco.MarkerSeverity.Error,
        message: `[${code}] ${msg}`,
        startLineNumber: l,
        startColumn: c,
        endLineNumber: l,
        endColumn: c + 1
      });
    }
    monaco.editor.setModelMarkers(model, 'compiscript', markers);
  }

  // Contador de errores
  const count = (res.errors || []).length;
  $('errorCount').textContent = count === 1 ? '1 error' : `${count} errores`;
  $('errorCount').className = 'chip ' + (count ? 'err' : 'ok');

  // Tabla de símbolos
  renderSymbols(res.symbols);

  // Cambiar a la pestaña adecuada
  if (count > 0) activateTab('errors'); else activateTab('symbols');

  setStatus('Listo', count ? 'warn' : 'ok');
}

// ===============================
// Symbols render
// ===============================
function escapeHtml(t) {
  return String(t ?? '').replace(/[&<>"']/g, s => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]
  ));
}

function renderSymbol(s) {
  const kind = `<span class="sym-kind">${escapeHtml(s?.kind || '')}</span>`;
  const name = `<span class="sym-name">${escapeHtml(s?.name || '(anon)')}</span>`;

  // Para funciones (top-level): params con nombre y tipo
  const params = (Array.isArray(s?.params) && s.params.length)
    ? '(' + s.params.map(p =>
        `${escapeHtml(p?.name || '')}: <span class="sym-type">${escapeHtml(p?.type || '')}</span>`
      ).join(', ') + ')'
    : '';

  const type = (s?.return_type)
    ? `: <span class="sym-type">${escapeHtml(s.return_type)}</span>`
    : (s?.type ? `: <span class="sym-type">${escapeHtml(s.type)}</span>` : '');

  let html = `<li>${kind} <code class="inline">${name}${params}${type}</code></li>`;

  // ---- Campos de clase ----
  if (Array.isArray(s?.fields) && s.fields.length) {
    html += `<ul class="sym-list nested">` +
      s.fields.map(f =>
        `<li>• <span class="sym-kind">Field</span> <code class="inline">` +
        `<span class="sym-name">${escapeHtml(f?.name)}</span>: ` +
        `<span class="sym-type">${escapeHtml(f?.type)}</span></code></li>`
      ).join('') +
      `</ul>`;
  }

  // ---- Métodos de clase ----
  if (Array.isArray(s?.methods) && s.methods.length) {
    html += `<ul class="sym-list nested">` +
      s.methods.map(m => {
        // En clases serializamos params como lista de strings (tipos)
        const sig = (Array.isArray(m?.params) && m.params.length)
          ? '(' + m.params.map(t => escapeHtml(t)).join(', ') + ')'
          : '()';
        const ret = m?.return_type ? ` → ${escapeHtml(m.return_type)}` : '';
        return `<li>• <span class="sym-kind">Method</span> <code class="inline">` +
               `<span class="sym-name">${escapeHtml(m?.name)}</span> ` +
               `<span class="sym-type">${sig}${ret}</span></code></li>`;
      }).join('') +
      `</ul>`;
  }

  return html;
}

function renderScope(node) {
  if (!node) return '<div class="muted">Sin tabla de símbolos disponible.</div>';
  const syms = Array.isArray(node.symbols) ? node.symbols : [];
  const children = Array.isArray(node.children) ? node.children : [];

  const title = `<div><strong>Scope:</strong> <code class="inline">${escapeHtml(node.scope_name || 'global')}</code></div>`;
  const list  = syms.length
    ? `<ul class="sym-list">${syms.map(renderSymbol).join('')}</ul>`
    : `<div class="muted">— sin símbolos —</div>`;
  const kids  = children.map(ch => `<div style="margin-left:10px">${renderScope(ch)}</div>`).join('');

  return `<div class="scope-block">${title}${list}${kids}</div>`;
}

function renderSymbols(root) {
  const el = $('symbols');
  el.innerHTML = '';
  if (!root) {
    el.innerHTML = '<div class="muted">Sin tabla de símbolos disponible.</div>';
    return;
  }
  el.innerHTML = renderScope(root);
}


// ===============================
// Splitter (redimensionar panel lateral)
// ===============================
function initSplitter() {
  const workspace = $('workspace');
  const splitter = $('splitter');
  let dragging = false;

  splitter.addEventListener('mousedown', (e) => {
    dragging = true; document.body.style.cursor = 'col-resize'; e.preventDefault();
  });
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const rect = workspace.getBoundingClientRect();
    const relX = e.clientX - rect.left;
    const minLeft = 380, maxLeft = rect.width - 320; // límites para editor
    const left = Math.max(minLeft, Math.min(maxLeft, relX));
    const rightCol = rect.width - left;
    workspace.style.gridTemplateColumns = `${left}px 6px ${rightCol}px`;
  });
  window.addEventListener('mouseup', () => {
    dragging = false; document.body.style.cursor = '';
  });
}
