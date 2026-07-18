/* ═══════════════════════════════════════════════════════════════
   KDP Puzzle Book Generator — Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ── State ───────────────────────────────────────────────────────────────────
let state = {
  selectedPuzzleId: null,
  selectedPuzzleName: '',
  currentPuzzleSvg: '',
  currentSolutionSvg: '',
  currentCluesSvg: '',
  currentTitle: '',
  currentInstructions: '',
  activeTab: 'puzzle',
  zoom: 1.0,
  batchList: [],
};

// Puzzles that need word input
const WORD_PUZZLES = new Set(['crossword', 'word_search']);

// Laberintos: único bloque con nivel "Kids" (muy fácil) en el selector de dificultad
const MAZE_PUZZLES = new Set(['maze_rect', 'maze_hex', 'maze_circular', 'maze_triangle',
                               'maze_triangle_sq', 'maze_weave', 'maze_round_weave']);

// Grosor de línea estándar único para todas las plantillas (KDP B&N)
const STROKE_STD = 1.5;
const CLUE_PUZZLES = new Set(['crossword']);

// Size options per puzzle type
const SIZE_OPTIONS = {
  sudoku_classic:        [{label:'9×9', value:9}],
  sudoku_16x16:          [{label:'16×16', value:16}],
  sudoku_killer:         [{label:'9×9', value:9}],
  sudoku_x:              [{label:'9×9', value:9}],
  sudoku_letters:        [{label:'9×9', value:9}],
  sudoku_jigsaw:         [{label:'9×9', value:9}],
  sudoku_jigsaw_x:       [{label:'9×9', value:9}],
  sudoku_jigsaw_letters: [{label:'9×9', value:9}],
  sudoku_12x12:          [{label:'12×12', value:12}],
  kenken:   [{label:'3×3',v:3},{label:'4×4',v:4},{label:'5×5',v:5},{label:'6×6',v:6},{label:'7×7',v:7},{label:'8×8',v:8}].map(o=>({label:o.label,value:o.v})),
  futoshiki:[{label:'4×4',value:4},{label:'5×5',value:5},{label:'6×6',value:6},{label:'7×7',value:7}],
  hitori:   [{label:'10×10',value:[10,10]},{label:'20×14',value:[20,14]}],
  hashi:    [{label:'20×14',value:[20,14]},{label:'18×25',value:[18,25]}],
  masyu:    [{label:'20×14',value:[20,14]},{label:'18×25',value:[18,25]}],
  akari:    [{label:'12×12',value:[12,12]},{label:'20×20',value:[20,20]}],
  nurikabe: [{label:'15×10',value:[15,10]}],
  crossword:[{label:'13×13',value:13},{label:'15×15',value:15},{label:'17×17',value:17},{label:'21×21',value:21}],
  word_search:[{label:'10×10',value:10},{label:'12×12',value:12},{label:'15×15',value:15},{label:'17×17',value:17},{label:'20×20',value:20}],
  maze_rect:[{label:'20×20',value:[20,20]},{label:'25×25',value:[25,25]},{label:'30×30',value:[30,30]}],
  maze_hex: [{label:'20×20',value:[20,20]},{label:'25×25',value:[25,25]},{label:'30×30',value:[30,30]}],
  maze_circular:[{label:'15 anillos',value:15},{label:'20 anillos',value:20},{label:'25 anillos',value:25},{label:'30 anillos',value:30}],
  maze_triangle:[{label:'20',value:20},{label:'25',value:25},{label:'30',value:30}],
  maze_triangle_sq:[{label:'20×40',value:[20,40]},{label:'25×50',value:[25,50]},{label:'30×60',value:[30,60]}],
  maze_weave:[{label:'15×15',value:[15,15]},{label:'18×18',value:[18,18]},{label:'20×20',value:[20,20]}],
  maze_round_weave:[{label:'15×15',value:[15,15]},{label:'18×18',value:[18,18]},{label:'20×20',value:[20,20]}],
};

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildSidebar();
});

function buildSidebar() {
  const tree = document.getElementById('puzzleTree');
  tree.innerHTML = '';
  CATALOG.categories.forEach(cat => {
    const item = document.createElement('div');
    item.className = 'category-item';
    item.innerHTML = `
      <div class="category-header" onclick="toggleCategory(this)">
        <span>${cat.label}</span>
        <span class="category-chevron">▶</span>
      </div>
      <div class="category-puzzles">
        ${cat.puzzles.map(p =>
          `<button class="puzzle-item" data-id="${p.id}" data-name="${p.name}"
                   onclick="selectPuzzle('${p.id}','${p.name.replace(/'/g,"\\'")}',${p.needs_words||false},${p.needs_clues||false})"
           >${p.name}</button>`
        ).join('')}
      </div>`;
    tree.appendChild(item);
  });
  // Open first category
  if (tree.firstChild) {
    tree.firstChild.classList.add('open');
  }
}

function toggleCategory(header) {
  header.parentElement.classList.toggle('open');
}

function selectPuzzle(id, name, needsWords, needsClues) {
  state.selectedPuzzleId = id;
  state.selectedPuzzleName = name;

  // Update sidebar active state
  document.querySelectorAll('.puzzle-item').forEach(el => el.classList.remove('active'));
  document.querySelector(`[data-id="${id}"]`)?.classList.add('active');

  // Update generate button
  document.getElementById('selectedName').textContent = name;
  document.getElementById('generateBtn').disabled = false;

  // Word/clue inputs
  const needsW = needsWords || WORD_PUZZLES.has(id);
  const needsC = needsClues || CLUE_PUZZLES.has(id);
  document.getElementById('wordsPanel').style.display = needsW ? 'flex' : 'none';
  document.getElementById('cluesCol').style.display = needsC ? 'block' : 'none';

  // Size selector
  buildSizeSelector(id);

  // Nivel "Kids" (muy fácil): solo disponible para laberintos
  updateDifficultyOptions(id);

  // Reset clues tab
  document.getElementById('cluesTabBtn').style.display = 'none';
}

function updateDifficultyOptions(id) {
  const sel = document.getElementById('difficulty');
  const hasKids = !!sel.querySelector('option[value="kids"]');
  if (MAZE_PUZZLES.has(id)) {
    if (!hasKids) {
      const opt = document.createElement('option');
      opt.value = 'kids';
      opt.textContent = 'Kids (muy fácil)';
      sel.insertBefore(opt, sel.firstChild);
    }
  } else if (hasKids) {
    if (sel.value === 'kids') sel.value = 'easy';
    sel.querySelector('option[value="kids"]').remove();
  }
}

function buildSizeSelector(id) {
  const sel = document.getElementById('sizeSelect');
  const opts = SIZE_OPTIONS[id] || [{label: 'Estándar', value: 9}];
  sel.innerHTML = opts.map(o => `<option value='${JSON.stringify(o.value)}'>${o.label}</option>`).join('');
}

// ── Generate ─────────────────────────────────────────────────────────────────
async function generatePuzzle() {
  if (!state.selectedPuzzleId) return;
  showLoading('Generando puzzle...');

  const sizeRaw = document.getElementById('sizeSelect').value;
  let size;
  try { size = JSON.parse(sizeRaw); } catch(e) { size = sizeRaw; }

  const payload = {
    puzzle_id:   state.selectedPuzzleId,
    style:       document.getElementById('style').value,
    difficulty:  document.getElementById('difficulty').value,
    stroke_width: STROKE_STD,
    size:        size,
    words:       document.getElementById('wordsInput').value,
    clues:       document.getElementById('cluesInput').value,
  };

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Error desconocido');

    state.currentPuzzleSvg    = data.puzzle_svg || '';
    state.currentSolutionSvg  = data.solution_svg || '';
    state.currentCluesSvg     = data.clues_svg || '';
    state.currentTitle        = data.title || state.selectedPuzzleName;
    state.currentInstructions = data.instructions || '';

    document.getElementById('previewTitle').textContent = state.currentTitle;
    document.getElementById('instructionsText').textContent = state.currentInstructions;
    document.getElementById('instructionsBox').style.display = state.currentInstructions ? 'block' : 'none';
    document.getElementById('exportBar').style.display = 'flex';

    if (state.currentCluesSvg) {
      document.getElementById('cluesTabBtn').style.display = 'inline-flex';
    }

    switchTab('puzzle', document.querySelector('.tab-btn'));
    state.zoom = 1.0;
    updateZoom();

  } catch(err) {
    alert('Error: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ── Preview tabs ──────────────────────────────────────────────────────────────
function switchTab(tab, btn) {
  state.activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  const canvas = document.getElementById('previewCanvas');
  let svg = '';
  if (tab === 'puzzle')   svg = state.currentPuzzleSvg;
  if (tab === 'solution') svg = state.currentSolutionSvg;
  if (tab === 'clues')    svg = state.currentCluesSvg;

  if (svg) {
    canvas.innerHTML = svg;
    const svgEl = canvas.querySelector('svg');
    if (svgEl) {
      svgEl.style.maxWidth = 'none';
      applyZoom(svgEl);
    }
  } else {
    canvas.innerHTML = `<div class="empty-state"><div class="empty-icon">▦</div>
      <div class="empty-text">Genera un puzzle primero</div></div>`;
  }
}

// ── Zoom ──────────────────────────────────────────────────────────────────────
function zoomPreview(delta) {
  state.zoom = Math.max(0.2, Math.min(4, state.zoom + delta));
  updateZoom();
}
function resetZoom() {
  state.zoom = 1.0;
  updateZoom();
}
function updateZoom() {
  document.getElementById('zoomVal').textContent = Math.round(state.zoom * 100) + '%';
  const svgEl = document.querySelector('#previewCanvas svg');
  if (svgEl) applyZoom(svgEl);
}
function applyZoom(svgEl) {
  svgEl.style.transform = `scale(${state.zoom})`;
}

// ── Export ────────────────────────────────────────────────────────────────────
async function exportFile(format, which) {
  if (!state.currentPuzzleSvg) { alert('Primero genera un puzzle.'); return; }
  showLoading(`Exportando ${format.toUpperCase()}...`);

  const payload = {
    format,
    which,
    puzzle_svg:   state.currentPuzzleSvg,
    solution_svg: state.currentSolutionSvg,
    clues_svg:    state.currentCluesSvg,
    title:        state.currentTitle,
    instructions: state.currentInstructions,
    book_size:    document.getElementById('bookSizeSelect').value,
    margin_type:  document.getElementById('marginType').value,
    stroke_width: STROKE_STD,
  };

  try {
    const res = await fetch('/api/export', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || res.statusText);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${state.currentTitle}_${which}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  } catch(err) {
    alert('Error al exportar: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ── Save pattern ──────────────────────────────────────────────────────────────
async function savePattern() {
  const name = prompt('Nombre del sub-patrón:', `${state.selectedPuzzleName} Custom`);
  if (!name) return;
  const payload = {
    id:    name.toLowerCase().replace(/\s+/g,'_'),
    name,
    base_puzzle:   state.selectedPuzzleId,
    style:         document.getElementById('style').value,
    stroke_weight: STROKE_STD,
    difficulty:    document.getElementById('difficulty').value,
    saved_by:      'user',
  };
  const res = await fetch('/api/patterns/save', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (data.ok) alert(`Sub-patrón "${name}" guardado en /puzzles_patterns/`);
}

// ── Batch Book ────────────────────────────────────────────────────────────────
function openBatchModal() {
  document.getElementById('batchOverlay').style.display = 'flex';
  renderBatchList();
}
function closeBatchModal() {
  document.getElementById('batchOverlay').style.display = 'none';
}

function addToBatch() {
  if (!state.selectedPuzzleId) { alert('Selecciona un tipo de puzzle primero.'); return; }
  const sizeRaw = document.getElementById('sizeSelect').value;
  let size;
  try { size = JSON.parse(sizeRaw); } catch(e) { size = sizeRaw; }

  state.batchList.push({
    puzzle_id:   state.selectedPuzzleId,
    name:        state.selectedPuzzleName,
    style:       document.getElementById('style').value,
    difficulty:  document.getElementById('difficulty').value,
    stroke_width: STROKE_STD,
    size,
    words: document.getElementById('wordsInput').value,
    clues: document.getElementById('cluesInput').value,
  });
  renderBatchList();
}

function removeBatch(idx) {
  state.batchList.splice(idx, 1);
  renderBatchList();
}

function renderBatchList() {
  const el = document.getElementById('batchList');
  if (!state.batchList.length) {
    el.innerHTML = '<div class="batch-empty">Añade puzzles al libro usando el botón de abajo.</div>';
    return;
  }
  el.innerHTML = state.batchList.map((item, i) => `
    <div class="batch-row">
      <div>
        <div class="batch-row-name">${i+1}. ${item.name}</div>
        <div class="batch-row-meta">${item.style} · ${item.difficulty}</div>
      </div>
      <button class="batch-row-remove" onclick="removeBatch(${i})">✕</button>
    </div>
  `).join('');
}

async function generateBatchPDF() {
  if (!state.batchList.length) { alert('Añade al menos un puzzle al libro.'); return; }
  closeBatchModal();
  showLoading('Generando PDF del libro... (puede tardar un momento)');

  const payload = {
    puzzles:    state.batchList,
    book_title: document.getElementById('bookTitle').value,
    author:     document.getElementById('bookAuthor').value,
    book_size:  document.getElementById('batchBookSize').value,
    margin_type: 'no_bleed',
  };

  try {
    const res = await fetch('/api/batch_pdf', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${payload.book_title}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  } catch(err) {
    alert('Error al generar PDF: ' + err.message);
  } finally {
    hideLoading();
  }
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function showLoading(msg) {
  document.getElementById('loadingText').textContent = msg || 'Procesando...';
  document.getElementById('loadingOverlay').style.display = 'flex';
}
function hideLoading() {
  document.getElementById('loadingOverlay').style.display = 'none';
}
