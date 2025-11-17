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

// Prueba TAC: activa la casilla TAC y analiza
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

  // Tabs (Errores / Símbolos / TAC)
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
  
  // Guardar preferencias de TAC
  const tacCheckbox = $('generateTAC');
  const optCheckbox = $('optimizeTAC');
  
  if (tacCheckbox) {
    tacCheckbox.checked = localStorage.getItem('generateTAC') === 'true';
    tacCheckbox.addEventListener('change', () => {
      localStorage.setItem('generateTAC', tacCheckbox.checked);
    });
  }
  
  if (optCheckbox) {
    optCheckbox.checked = localStorage.getItem('optimizeTAC') === 'true';
    optCheckbox.addEventListener('change', () => {
      localStorage.setItem('optimizeTAC', optCheckbox.checked);
      // Optimizar solo tiene sentido si TAC está activado
      if (optCheckbox.checked && tacCheckbox && !tacCheckbox.checked) {
        tacCheckbox.checked = true;
        localStorage.setItem('generateTAC', 'true');
      }
    });
  }
}

function activateTab(name) {
  for (const t of document.querySelectorAll('.tab')) {
    t.classList.toggle('active', t.dataset.tab === name);
  }
  $('errors').style.display = (name === 'errors') ? 'block' : 'none';
  $('symbols').style.display = (name === 'symbols') ? 'block' : 'none';
  $('tac').style.display = (name === 'tac') ? 'block' : 'none';
}

function setTheme(mode) {
  document.documentElement.setAttribute('data-theme', mode);
  localStorage.setItem('theme', mode);
  monaco.editor.setTheme(mode === 'dark' ? 'vs-dark' : 'vs');
}

function updateThemeButtonText(mode) {
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
  const generateTAC = $('generateTAC')?.checked || false;
  const optimizeTAC = $('optimizeTAC')?.checked || false;

  setStatus('Analizando…');
  let res;
  try {
    const r = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        source,
        generate_tac: generateTAC,
        optimize_tac: optimizeTAC
      })
    });
    res = await r.json();
  } catch (e) {
    res = { 
      ok: false, 
      errors: [{ code:'NET', message:String(e), line:1, column:1 }], 
      symbols: null,
      tac: null
    };
  }

  // Limpiar markers
  monaco.editor.setModelMarkers(model, 'compiscript', []);

  const panel = $('errors');
  panel.innerHTML = '';

  if (res.ok) {
    panel.innerHTML = `<div class="msg-ok">✔ Sin errores</div>`;
    
    // Si se generó TAC, mostrar estadísticas
    if (res.tac && res.tac.stats) {
      const stats = res.tac.stats;
      panel.innerHTML += `
        <div style="margin-top: 12px; padding: 8px; background: var(--chip); border-radius: 8px;">
          <strong>TAC generado:</strong><br/>
          ${stats.instructions} instrucciones, ${stats.temporals} temporales, ${stats.labels} etiquetas
        </div>
      `;
    }
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
  
  // Código TAC
  renderTAC(res.tac);

  // Cambiar a la pestaña adecuada
  if (count > 0) {
    activateTab('errors');
  } else if (res.tac) {
    activateTab('tac');
  } else {
    activateTab('symbols');
  }

  setStatus('Listo', count ? 'warn' : 'ok');
}

// ===============================
// TAC render
// ===============================
function renderTAC(tacData) {
  const el = $('tac');
  if (!el) return;
  
  el.innerHTML = '';
  
  if (!tacData || !tacData.code) {
    el.innerHTML = '<div class="muted">Código TAC no generado. Active la casilla TAC y analice.</div>';
    return;
  }
  
  // Estadísticas
  if (tacData.stats) {
    const stats = tacData.stats;
    const statsDiv = document.createElement('div');
    statsDiv.className = 'tac-stats';
    statsDiv.innerHTML = `
      <span>📊 Instrucciones: <strong>${stats.instructions}</strong></span>
      <span>🔢 Temporales: <strong>${stats.temporals}</strong></span>
      <span>🏷️ Etiquetas: <strong>${stats.labels}</strong></span>
    `;
    el.appendChild(statsDiv);
  }
  
  // Código TAC
  const codeDiv = document.createElement('div');
  codeDiv.className = 'tac-code';
  codeDiv.textContent = tacData.code.join('\n');
  el.appendChild(codeDiv);
  
  // Botón para copiar
  const copyBtn = document.createElement('button');
  copyBtn.className = 'btn';
  copyBtn.style.marginTop = '8px';
  copyBtn.textContent = '📋 Copiar TAC';
  copyBtn.onclick = () => {
    navigator.clipboard.writeText(tacData.code.join('\n'));
    toast('TAC copiado al portapapeles', 'ok');
  };
  el.appendChild(copyBtn);
}

// ===============================
// Symbols render (mantenemos el original)
// ===============================
function escapeHtml(t) {
  return String(t ?? '').replace(/[&<>"']/g, s => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]
  ));
}

function renderSymbol(s) {
  const kind = `<span class="sym-kind">${escapeHtml(s?.kind || '')}</span>`;
  const name = `<span class="sym-name">${escapeHtml(s?.name || '(anon)')}</span>`;

  // Construir parámetros CON OFFSETS
  const params = (Array.isArray(s?.params) && s.params.length)
    ? '(' + s.params.map(p => {
        let pstr = `${escapeHtml(p?.name || '')}: <span class="sym-type">${escapeHtml(p?.type || '')}</span>`;
        // Mostrar offset del parámetro
        if (p?.offset !== null && p?.offset !== undefined) {
          pstr += ` <span style="color: #f6c85f; font-size: 10px;">[offset=${p.offset}]</span>`;
        }
        return pstr;
      }).join(', ') + ')'
    : '';

  const type = (s?.return_type)
    ? `: <span class="sym-type">${escapeHtml(s.return_type)}</span>`
    : (s?.type ? `: <span class="sym-type">${escapeHtml(s.type)}</span>` : '');

  let html = `<li>${kind} <code class="inline">${name}${params}${type}`;

  // OFFSET para variables
  if (s?.offset !== null && s?.offset !== undefined) {
    html += ` <span style="color: #4cc9f0; font-size: 10px; font-weight: bold;">[offset=${s.offset}]</span>`;
  }

  // LABEL para funciones
  if (s?.label) {
    html += ` <span style="color: #00e5a8; font-size: 10px; font-weight: bold;">[${escapeHtml(s.label)}]</span>`;
  }

  html += `</code>`;

  // REGISTRO DE ACTIVACIÓN para funciones
  // Los campos están directamente en 's', no en 's.activation_record'
  if (s?.frame_size !== null && s?.frame_size !== undefined && s?.frame_size > 0) {
    html += `<br/><span style="margin-left: 20px; font-size: 11px; color: var(--muted);">`;
    html += `📦 Frame: ${s.frame_size}B (params: ${s.params_size || 0}B, locals: ${s.locals_size || 0}B)`;
    html += `</span>`;
  }

  // TAMAÑO DE INSTANCIA para clases
  if (s?.instance_size !== null && s?.instance_size !== undefined && s?.instance_size > 0) {
    html += `<br/><span style="margin-left: 20px; font-size: 11px; color: var(--muted);">`;
    html += `📏 Instance: ${s.instance_size} bytes`;
    html += `</span>`;
  }

  html += `</li>`;

  // Fields
  if (Array.isArray(s?.fields) && s.fields.length) {
    html += `<ul class="sym-list nested">` +
      s.fields.map(f =>
        `<li>• <span class="sym-kind">Field</span> <code class="inline">` +
        `<span class="sym-name">${escapeHtml(f?.name)}</span>: ` +
        `<span class="sym-type">${escapeHtml(f?.type)}</span></code></li>`
      ).join('') +
      `</ul>`;
  }

  // Methods
  if (Array.isArray(s?.methods) && s.methods.length) {
    html += `<ul class="sym-list nested">` +
      s.methods.map(m => {
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
  
  // DEBUG: Ver qué datos llegan
  console.log("=== DATOS RECIBIDOS ===");
  console.log("Root completo:", root);
  if (root.symbols) {
    root.symbols.forEach(s => {
      console.log(`\nSímbolo: ${s.name} (${s.kind})`);
      console.log("  offset:", s.offset);
      console.log("  label:", s.label);
      console.log("  activation_record:", s.activation_record);
      if (s.params) {
        s.params.forEach(p => {
          console.log(`  param ${p.name}: offset=${p.offset}`);
        });
      }
    });
  }
  console.log("=======================");
  
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
    const minLeft = 380, maxLeft = rect.width - 320;
    const left = Math.max(minLeft, Math.min(maxLeft, relX));
    const rightCol = rect.width - left;
    workspace.style.gridTemplateColumns = `${left}px 6px ${rightCol}px`;
  });
  window.addEventListener('mouseup', () => {
    dragging = false; document.body.style.cursor = '';
  });
}