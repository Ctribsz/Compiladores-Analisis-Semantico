// Cargar Monaco y crear el editor
let editor, model;

require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor@0.45.0/min/vs' } });
require(['vs/editor/editor.main'], function () {

  const sample = `// Bienvenido a Compiscript IDE
let x: integer = 2;
function add(a: integer, b: integer): integer { return a + b; }
let z: integer = add(1, 2);

// Proba un error:
// if (x) { }  // <- cond no booleana
`;

  editor = monaco.editor.create(document.getElementById('editor'), {
    value: sample,
    language: 'typescript',    // highlight aproximado
    automaticLayout: true,
    minimap: { enabled: false },
    fontSize: 14
  });

  model = editor.getModel();

  // Atajo Ctrl/Cmd+Enter
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, analyze);

  document.getElementById('analyze').addEventListener('click', analyze);
});

async function analyze() {
  const source = editor.getValue();
  const res = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source })
  }).then(r => r.json()).catch(e => ({ ok:false, errors:[{ code:'NET', message:String(e), line:1, column:1 }]}));

  // Limpiar markers
  monaco.editor.setModelMarkers(model, 'compiscript', []);

  const panel = document.getElementById('errors');
  panel.innerHTML = '';

  if (res.ok) {
    panel.innerHTML = `<div class="ok">✔ Sin errores</div>`;
    return;
  }

  // Mostrar lista y markers
  const markers = [];
  for (const err of res.errors) {
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