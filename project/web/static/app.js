/* app.js — StegoTool Frontend Logic */

const API = '';   // same origin (Flask serves both)

// ── Pixel grid animation ────────────────────────────────────────────────
(function initPixelGrid() {
  const grid = document.getElementById('pixelGrid');
  if (!grid) return;
  const count = 20 * 20;
  const colors = ['#0a0c10','#0f1218','#161b24','#00d4ff','#7c3aed','#00ff88'];
  for (let i = 0; i < count; i++) {
    const px = document.createElement('div');
    px.className = 'px';
    grid.appendChild(px);
  }
  const pxEls = grid.querySelectorAll('.px');
  function flicker() {
    const idx = Math.floor(Math.random() * count);
    const col = colors[Math.floor(Math.random() * colors.length)];
    pxEls[idx].style.background = col;
    setTimeout(flicker, Math.random() * 80 + 20);
  }
  flicker();
})();

// ── Drop zone setup ─────────────────────────────────────────────────────
function setupDropZone(dzId, inputId, previewId, opts = {}) {
  const dz    = document.getElementById(dzId);
  const input = document.getElementById(inputId);
  if (!dz || !input) return;

  dz.addEventListener('click', () => input.click());

  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault();
    dz.classList.remove('drag-over');
    if (e.dataTransfer.files.length) {
      input.files = e.dataTransfer.files;
      handleFileSelected(input, dz, previewId, opts);
    }
  });

  input.addEventListener('change', () => handleFileSelected(input, dz, previewId, opts));
}

function handleFileSelected(input, dz, previewId, opts) {
  const file = input.files[0];
  if (!file) return;
  dz.classList.add('has-file');
  dz.querySelector('span').textContent = '✓ ' + file.name;

  // Show info for non-image files
  if (opts.infoId) {
    const info = document.getElementById(opts.infoId);
    if (info) info.textContent = `${file.name} — ${formatBytes(file.size)}`;
  }

  // Image preview
  if (previewId && file.type.startsWith('image/')) {
    const wrap = document.getElementById(previewId);
    if (wrap) {
      wrap.innerHTML = '';
      const img = document.createElement('img');
      img.src = URL.createObjectURL(file);
      wrap.appendChild(img);
    }
  }
}

function formatBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024*1024) return (b/1024).toFixed(1) + ' KB';
  return (b/1024/1024).toFixed(2) + ' MB';
}

// ── Init all drop zones ─────────────────────────────────────────────────
setupDropZone('dz-cover-text',  'cover-text-file',   'prev-cover-text');
setupDropZone('dz-stego-text',  'stego-text-file',   'prev-stego-text');
setupDropZone('dz-pubkey',      'pubkey-file',        null);
setupDropZone('dz-privkey',     'privkey-file',       null);
setupDropZone('dz-cover-img',   'cover-img-file',    'prev-cover-img');
setupDropZone('dz-secret-img',  'secret-img-file',   'prev-secret-img');
setupDropZone('dz-stego-img',   'stego-img-file',    'prev-stego-img');
setupDropZone('dz-cover-file',  'cover-file-img',    'prev-cover-file');
setupDropZone('dz-secret-file', 'secret-file-input', null, { infoId: 'secret-file-info' });
setupDropZone('dz-stego-file',  'stego-file-img',    'prev-stego-file');
setupDropZone('dz-analyze',     'analyze-file',      'prev-analyze');

// ── Toggle encryption panels ────────────────────────────────────────────
document.getElementById('encrypt-text-toggle').addEventListener('change', function () {
  document.getElementById('pubkey-upload').style.display = this.checked ? 'block' : 'none';
});
document.getElementById('decrypt-text-toggle').addEventListener('change', function () {
  document.getElementById('privkey-upload').style.display = this.checked ? 'block' : 'none';
});

// ── Helpers ─────────────────────────────────────────────────────────────
function setLoading(resultId, btnEl) {
  document.getElementById(resultId).innerHTML = '';
  if (btnEl) { btnEl.disabled = true; btnEl.innerHTML = '<span class="spinner"></span> Working...'; }
}

function resetBtn(btnEl, originalHTML) {
  if (btnEl) { btnEl.disabled = false; btnEl.innerHTML = originalHTML; }
}

function showSuccess(resultId, rows, downloadFile = null) {
  let html = `<div class="result-success">
    <div class="result-title ok">✅ Success</div>`;
  for (const [label, value] of rows) {
    html += `<div class="result-row">
      <span class="result-label">${label}</span>
      <span class="result-value">${value}</span>
    </div>`;
  }
  if (downloadFile) {
    html += `<a class="download-btn" href="/download/${encodeURIComponent(downloadFile)}" download>
      ⬇ Download Result</a>`;
  }
  html += `</div>`;
  document.getElementById(resultId).innerHTML = html;
}

function showError(resultId, msg) {
  document.getElementById(resultId).innerHTML = `
    <div class="result-error">
      <div class="result-title err">❌ Error</div>
      ${msg}
    </div>`;
}

async function postForm(url, formData) {
  const res  = await fetch(API + url, { method: 'POST', body: formData });
  return res.json();
}

// ── ENCODE TEXT ─────────────────────────────────────────────────────────
async function encodeText() {
  const btn = document.querySelector('#encode-text .btn');
  const orig = btn.innerHTML;
  setLoading('result-encode-text', btn);

  try {
    const cover   = document.getElementById('cover-text-file').files[0];
    const message = document.getElementById('encode-text-msg').value.trim();
    const encrypt = document.getElementById('encrypt-text-toggle').checked;
    const pubkey  = document.getElementById('pubkey-file').files[0];

    if (!cover)   return showError('result-encode-text', 'Please select a cover image.');
    if (!message) return showError('result-encode-text', 'Please enter a message.');
    if (encrypt && !pubkey) return showError('result-encode-text', 'Please upload your public key.');

    const fd = new FormData();
    fd.append('cover', cover);
    fd.append('message', message);
    fd.append('encrypt', encrypt ? 'true' : 'false');
    if (pubkey) fd.append('pubkey', pubkey);

    const data = await postForm('/api/encode-text', fd);
    if (data.error) return showError('result-encode-text', data.error);

    showSuccess('result-encode-text', [
      ['Capacity used', data.usage_pct + '%'],
      ['Encrypted',     data.encrypted ? 'Yes (RSA+AES-256-GCM)' : 'No'],
      ['Output file',   data.file],
    ], data.file);
  } catch (e) {
    showError('result-encode-text', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── DECODE TEXT ─────────────────────────────────────────────────────────
async function decodeText() {
  const btn = document.querySelector('#decode-text .btn');
  const orig = btn.innerHTML;
  setLoading('result-decode-text', btn);

  try {
    const stego   = document.getElementById('stego-text-file').files[0];
    const decrypt = document.getElementById('decrypt-text-toggle').checked;
    const privkey = document.getElementById('privkey-file').files[0];

    if (!stego) return showError('result-decode-text', 'Please select a stego image.');
    if (decrypt && !privkey) return showError('result-decode-text', 'Please upload your private key.');

    const fd = new FormData();
    fd.append('stego', stego);
    fd.append('decrypt', decrypt ? 'true' : 'false');
    if (privkey) fd.append('privkey', privkey);

    const data = await postForm('/api/decode-text', fd);
    if (data.error) return showError('result-decode-text', data.error);

    showSuccess('result-decode-text', [
      ['Message',   `<strong style="color:#00ff88">${escapeHtml(data.message)}</strong>`],
      ['Encrypted', data.encrypted ? 'Yes — decrypted successfully' : 'No'],
    ]);
  } catch (e) {
    showError('result-decode-text', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── ENCODE IMAGE ─────────────────────────────────────────────────────────
async function encodeImage() {
  const btn = document.querySelector('#encode-image .btn');
  const orig = btn.innerHTML;
  setLoading('result-encode-image', btn);

  try {
    const cover  = document.getElementById('cover-img-file').files[0];
    const secret = document.getElementById('secret-img-file').files[0];
    if (!cover)  return showError('result-encode-image', 'Please select a cover image.');
    if (!secret) return showError('result-encode-image', 'Please select a secret image.');

    const fd = new FormData();
    fd.append('cover', cover); fd.append('secret', secret);

    const data = await postForm('/api/encode-image', fd);
    if (data.error) return showError('result-encode-image', data.error);

    showSuccess('result-encode-image', [
      ['Cover size',  data.cover_size],
      ['Secret size', data.secret_size],
      ['Output file', data.file],
    ], data.file);
  } catch (e) {
    showError('result-encode-image', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── DECODE IMAGE ──────────────────────────────────────────────────────────
async function decodeImage() {
  const btn = document.querySelector('#decode-image .btn');
  const orig = btn.innerHTML;
  setLoading('result-decode-image', btn);

  try {
    const stego = document.getElementById('stego-img-file').files[0];
    if (!stego) return showError('result-decode-image', 'Please select a stego image.');

    const fd = new FormData();
    fd.append('stego', stego);

    const data = await postForm('/api/decode-image', fd);
    if (data.error) return showError('result-decode-image', data.error);

    showSuccess('result-decode-image', [
      ['Secret size', data.secret_size],
      ['Output file', data.file],
    ], data.file);
  } catch (e) {
    showError('result-decode-image', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── ENCODE FILE ───────────────────────────────────────────────────────────
async function encodeFile() {
  const btn = document.querySelector('#encode-file .btn');
  const orig = btn.innerHTML;
  setLoading('result-encode-file', btn);

  try {
    const cover  = document.getElementById('cover-file-img').files[0];
    const secret = document.getElementById('secret-file-input').files[0];
    if (!cover)  return showError('result-encode-file', 'Please select a cover image.');
    if (!secret) return showError('result-encode-file', 'Please select a file to hide.');

    const fd = new FormData();
    fd.append('cover', cover); fd.append('secret', secret);

    const data = await postForm('/api/encode-file', fd);
    if (data.error) return showError('result-encode-file', data.error);

    showSuccess('result-encode-file', [
      ['Hidden file',    data.filename],
      ['File size',      formatBytes(data.file_size)],
      ['Capacity used',  data.usage_pct + '%'],
      ['Output file',    data.file],
    ], data.file);
  } catch (e) {
    showError('result-encode-file', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── DECODE FILE ───────────────────────────────────────────────────────────
async function decodeFile() {
  const btn = document.querySelector('#decode-file .btn');
  const orig = btn.innerHTML;
  setLoading('result-decode-file', btn);

  try {
    const stego = document.getElementById('stego-file-img').files[0];
    if (!stego) return showError('result-decode-file', 'Please select a stego image.');

    const fd = new FormData();
    fd.append('stego', stego);

    const data = await postForm('/api/decode-file', fd);
    if (data.error) return showError('result-decode-file', data.error);

    showSuccess('result-decode-file', [
      ['Filename',  data.filename],
      ['File size', formatBytes(data.file_size)],
    ], data.file);
  } catch (e) {
    showError('result-decode-file', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── ANALYZE ───────────────────────────────────────────────────────────────
async function analyzeImage() {
  const btn = document.querySelector('#analyze .btn');
  const orig = btn.innerHTML;
  setLoading('result-analyze', btn);

  try {
    const image = document.getElementById('analyze-file').files[0];
    if (!image) return showError('result-analyze', 'Please select an image to analyze.');

    const fd = new FormData();
    fd.append('image', image);

    const data = await postForm('/api/analyze', fd);
    if (data.error) return showError('result-analyze', data.error);

    const v = data.final_verdict;
    const lsb = data.lsb_analysis;
    const chi = data.chi_square;

    let html = `<div class="result-success">
      <span class="analysis-verdict verdict-${v}">${v.replace('_', ' ')}</span>
      <div class="result-row">
        <span class="result-label">Confidence</span>
        <span class="result-value">${data.confidence}%</span>
      </div>
      <div class="result-row">
        <span class="result-label">Summary</span>
        <span class="result-value">${data.summary}</span>
      </div>

      <div class="analysis-section">
        <h4>LSB ENTROPY ANALYSIS</h4>
        <div class="result-row">
          <span class="result-label">Avg entropy</span>
          <span class="result-value">${lsb.avg_entropy} <span style="color:var(--text-dim);font-size:.8rem">(>0.97 = suspicious)</span></span>
        </div>`;

    for (const [ch, d] of Object.entries(lsb.channels)) {
      const flag = d.verdict === 'suspicious' ? '<span class="ch-flag-sus">⚠ suspicious</span>' : '<span class="ch-flag-ok">✓ normal</span>';
      html += `<div class="ch-row">
        <span class="ch-name">${ch}</span>
        <span>entropy: ${d.entropy}</span>
        <span>ones: ${d.ones_pct}%</span>
        ${flag}
      </div>`;
    }

    html += `</div><div class="analysis-section">
        <h4>CHI-SQUARE STATISTICAL TEST</h4>
        <div class="result-row">
          <span class="result-label">Suspicious channels</span>
          <span class="result-value">${chi.suspicious_channels}/3</span>
        </div>
        <div class="result-row">
          <span class="result-label">Avg p-value</span>
          <span class="result-value">${chi.avg_p_value} <span style="color:var(--text-dim);font-size:.8rem">(&lt;0.05 = suspicious)</span></span>
        </div>`;

    for (const [ch, d] of Object.entries(chi.channels)) {
      const flag = d.verdict === 'suspicious' ? '<span class="ch-flag-sus">⚠ suspicious</span>' : '<span class="ch-flag-ok">✓ normal</span>';
      html += `<div class="ch-row">
        <span class="ch-name">${ch}</span>
        <span>χ²=${d.chi_square}</span>
        <span>p=${d.p_value}</span>
        ${flag}
      </div>`;
    }

    html += `</div></div>`;
    document.getElementById('result-analyze').innerHTML = html;

  } catch (e) {
    showError('result-analyze', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── KEY GENERATION ────────────────────────────────────────────────────────
async function generateKeys() {
  const btn = document.querySelector('#keygen .btn');
  const orig = btn.innerHTML;
  setLoading('result-keygen', btn);

  try {
    const data = await postForm('/api/keygen', new FormData());
    if (data.error) return showError('result-keygen', data.error);

    document.getElementById('result-keygen').innerHTML = `
      <div class="result-success">
        <div class="result-title ok">✅ Key Pair Generated</div>
        <div class="result-row">
          <span class="result-label">Algorithm</span>
          <span class="result-value">RSA-2048 + AES-256-GCM</span>
        </div>

        <div style="margin-top:1rem">
          <div style="font-weight:700;color:#fff;margin-bottom:.4rem">🔑 Public Key (share this)</div>
          <div class="key-box">${escapeHtml(data.public_pem)}</div>
          <a class="download-btn" href="/download/${encodeURIComponent(data.public_key)}" download style="margin-top:.5rem">
            ⬇ Download public.pem
          </a>
        </div>

        <div style="margin-top:1rem">
          <div style="font-weight:700;color:#ff4444;margin-bottom:.4rem">🔒 Private Key (keep secret!)</div>
          <div class="key-box">${escapeHtml(data.private_pem)}</div>
          <a class="download-btn" href="/download/${encodeURIComponent(data.private_key)}" download style="margin-top:.5rem;background:var(--red);color:#fff">
            ⬇ Download private.pem
          </a>
        </div>
      </div>`;
  } catch (e) {
    showError('result-keygen', e.message);
  } finally {
    resetBtn(btn, orig);
  }
}

// ── Utils ─────────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
