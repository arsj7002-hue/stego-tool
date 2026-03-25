/* app.js — StegoTool Frontend */

const API = '';

// ── Boot Sequence ──────────────────────────────────────────────────────────
const bootMessages = [
  'INITIALIZING SECURE CHANNEL...',
  'LOADING CRYPTOGRAPHIC MODULES...',
  'ESTABLISHING LSB ENCODER...',
  'VERIFYING RSA KEY FRAMEWORK...',
  'ALL SYSTEMS OPERATIONAL.',
];
let bootIdx = 0;
const bootFill = document.getElementById('bootFill');
const bootText = document.getElementById('bootText');
const bootOverlay = document.getElementById('bootOverlay');

function runBoot() {
  let pct = 0;
  const interval = setInterval(() => {
    pct += 2;
    bootFill.style.width = pct + '%';
    if (pct % 20 === 0 && bootIdx < bootMessages.length) {
      bootText.textContent = bootMessages[bootIdx++];
    }
    if (pct >= 100) {
      clearInterval(interval);
      setTimeout(() => bootOverlay.classList.add('hidden'), 300);
    }
  }, 25);
}
runBoot();

// ── Clock ──────────────────────────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent =
    String(now.getHours()).padStart(2,'0') + ':' +
    String(now.getMinutes()).padStart(2,'0') + ':' +
    String(now.getSeconds()).padStart(2,'0');
}
updateClock();
setInterval(updateClock, 1000);

// ── Particle Canvas ────────────────────────────────────────────────────────
(function initParticles() {
  const canvas = document.getElementById('particles');
  const ctx    = canvas.getContext('2d');
  let W, H, particles = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  function Particle() {
    this.x    = Math.random() * W;
    this.y    = Math.random() * H;
    this.vx   = (Math.random() - 0.5) * 0.3;
    this.vy   = (Math.random() - 0.5) * 0.3;
    this.size = Math.random() * 1.5 + 0.5;
    this.alpha= Math.random() * 0.5 + 0.1;
    this.color= Math.random() > 0.7 ? '#f0b429' : '#00e5cc';
  }
  Particle.prototype.update = function() {
    this.x += this.vx; this.y += this.vy;
    if (this.x < 0) this.x = W;
    if (this.x > W) this.x = 0;
    if (this.y < 0) this.y = H;
    if (this.y > H) this.y = 0;
  };

  for (let i = 0; i < 80; i++) particles.push(new Particle());

  function draw() {
    ctx.clearRect(0, 0, W, H);
    // Draw connections
    for (let i = 0; i < particles.length; i++) {
      for (let j = i+1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 100) {
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0,229,204,${0.04 * (1 - dist/100)})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
    // Draw dots
    particles.forEach(p => {
      p.update();
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
      ctx.globalAlpha = 1;
    });
    requestAnimationFrame(draw);
  }
  draw();
})();

// ── Tab Switching ──────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === name);
  });
  document.querySelectorAll('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === 'tab-' + name);
  });
}

// ── Drop Zones ────────────────────────────────────────────────────────────
function setupDZ(dzId, inputId, previewId, opts = {}) {
  const dz    = document.getElementById(dzId);
  const input = document.getElementById(inputId);
  if (!dz || !input) return;

  dz.addEventListener('dragover',  e => { e.preventDefault(); dz.classList.add('drag-over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) { input.files = e.dataTransfer.files; onFile(input, dz, previewId, opts); }
  });
  input.addEventListener('change', () => onFile(input, dz, previewId, opts));
}

function onFile(input, dz, previewId, opts) {
  const file = input.files[0];
  if (!file) return;
  dz.classList.add('has-file');
  dz.querySelector('.dz-text').textContent = '✓ ' + file.name;

  if (opts.chipId) {
    const chip = document.getElementById(opts.chipId);
    if (chip) { chip.textContent = file.name + ' — ' + fmtBytes(file.size); chip.classList.add('visible'); }
  }
  if (previewId && file.type.startsWith('image/')) {
    const wrap = document.getElementById(previewId);
    if (wrap) { wrap.innerHTML = ''; const img = document.createElement('img'); img.src = URL.createObjectURL(file); wrap.appendChild(img); }
  }
}

function fmtBytes(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(2) + ' MB';
}

// Init all drop zones
setupDZ('dz-cover-text',  'cover-text-file',   'prev-cover-text');
setupDZ('dz-stego-text',  'stego-text-file',   'prev-stego-text');
setupDZ('dz-pubkey',      'pubkey-file',        null);
setupDZ('dz-privkey',     'privkey-file',       null);
setupDZ('dz-cover-img',   'cover-img-file',    'prev-cover-img');
setupDZ('dz-secret-img',  'secret-img-file',   'prev-secret-img');
setupDZ('dz-stego-img',   'stego-img-file',    'prev-stego-img');
setupDZ('dz-cover-file',  'cover-file-img',    'prev-cover-file');
setupDZ('dz-secret-file', 'secret-file-input', null, { chipId: 'secret-file-info' });
setupDZ('dz-stego-file',  'stego-file-img',    'prev-stego-file');

// ── Char counter ──────────────────────────────────────────────────────────
document.getElementById('encode-text-msg').addEventListener('input', function() {
  document.getElementById('char-count').textContent = this.value.length;
});

// ── Encryption toggles ────────────────────────────────────────────────────
document.getElementById('encrypt-text-toggle').addEventListener('change', function() {
  const s = document.getElementById('pubkey-section');
  s.classList.toggle('open', this.checked);
});
document.getElementById('decrypt-text-toggle').addEventListener('change', function() {
  const s = document.getElementById('privkey-section');
  s.classList.toggle('open', this.checked);
});

// ── API helpers ────────────────────────────────────────────────────────────
async function post(url, fd) {
  const res = await fetch(API + url, { method: 'POST', body: fd });
  return res.json();
}

function loading(btnEl) {
  const orig = btnEl.innerHTML;
  btnEl.disabled = true;
  btnEl.innerHTML = `<span class="spinner"></span><span>PROCESSING...</span>`;
  return orig;
}
function restore(btnEl, orig) { btnEl.disabled = false; btnEl.innerHTML = orig; }

function ok(zoneId, rows, dlFile, isGold) {
  const color = isGold ? 'gold' : 'teal';
  let h = `<div class="result-ok"><div class="result-title ${color}">◆ OPERATION COMPLETE</div>`;
  rows.forEach(([l, v]) => h += `<div class="result-row"><span class="rl">${l}</span><span class="rv">${v}</span></div>`);
  if (dlFile) h += `<a class="dl-btn" href="/download/${encodeURIComponent(dlFile)}" download>⬇ DOWNLOAD RESULT</a>`;
  h += `</div>`;
  document.getElementById(zoneId).innerHTML = h;
}

function err(zoneId, msg) {
  document.getElementById(zoneId).innerHTML =
    `<div class="result-err"><div class="result-title err">✕ ERROR</div>${esc(msg)}</div>`;
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── ENCODE TEXT ────────────────────────────────────────────────────────────
async function encodeText() {
  const btn  = document.querySelector('#card-encode-text .op-btn');
  const orig = loading(btn);
  try {
    const cover   = document.getElementById('cover-text-file').files[0];
    const message = document.getElementById('encode-text-msg').value.trim();
    const encrypt = document.getElementById('encrypt-text-toggle').checked;
    const pubkey  = document.getElementById('pubkey-file').files[0];

    if (!cover)   return err('result-encode-text', 'Select a cover image first.');
    if (!message) return err('result-encode-text', 'Enter a message to hide.');
    if (encrypt && !pubkey) return err('result-encode-text', 'Upload your public key for encryption.');

    const fd = new FormData();
    fd.append('cover', cover); fd.append('message', message);
    fd.append('encrypt', encrypt ? 'true' : 'false');
    if (pubkey) fd.append('pubkey', pubkey);

    const d = await post('/api/encode-text', fd);
    if (d.error) return err('result-encode-text', d.error);

    ok('result-encode-text', [
      ['CAPACITY USED', d.usage_pct + '%'],
      ['ENCRYPTED',     d.encrypted ? 'RSA+AES-256-GCM ✓' : 'None (plaintext)'],
      ['OUTPUT FILE',   d.file],
    ], d.file);
  } catch(e) { err('result-encode-text', e.message); }
  finally    { restore(btn, orig); }
}

// ── DECODE TEXT ────────────────────────────────────────────────────────────
async function decodeText() {
  const btn  = document.querySelector('#card-decode-text .op-btn');
  const orig = loading(btn);
  try {
    const stego   = document.getElementById('stego-text-file').files[0];
    const decrypt = document.getElementById('decrypt-text-toggle').checked;
    const privkey = document.getElementById('privkey-file').files[0];

    if (!stego) return err('result-decode-text', 'Select the stego image.');
    if (decrypt && !privkey) return err('result-decode-text', 'Upload your private key.');

    const fd = new FormData();
    fd.append('stego', stego);
    fd.append('decrypt', decrypt ? 'true' : 'false');
    if (privkey) fd.append('privkey', privkey);

    const d = await post('/api/decode-text', fd);
    if (d.error) return err('result-decode-text', d.error);

    document.getElementById('result-decode-text').innerHTML = `
      <div class="result-ok">
        <div class="result-title gold">◆ MESSAGE REVEALED</div>
        <div class="result-row"><span class="rl">ENCRYPTED</span><span class="rv">${d.encrypted ? 'Yes — decrypted ✓' : 'No'}</span></div>
        <div class="msg-reveal">${esc(d.message)}</div>
      </div>`;
  } catch(e) { err('result-decode-text', e.message); }
  finally    { restore(btn, orig); }
}

// ── ENCODE IMAGE ───────────────────────────────────────────────────────────
async function encodeImage() {
  const btn  = document.querySelector('#tab-image .op-btn.teal');
  const orig = loading(btn);
  try {
    const cover  = document.getElementById('cover-img-file').files[0];
    const secret = document.getElementById('secret-img-file').files[0];
    if (!cover)  return err('result-encode-image', 'Select a cover image.');
    if (!secret) return err('result-encode-image', 'Select the secret image to hide.');

    const fd = new FormData();
    fd.append('cover', cover); fd.append('secret', secret);
    const d = await post('/api/encode-image', fd);
    if (d.error) return err('result-encode-image', d.error);

    ok('result-encode-image', [
      ['COVER SIZE',  d.cover_size],
      ['SECRET SIZE', d.secret_size],
      ['OUTPUT',      d.file],
    ], d.file);
  } catch(e) { err('result-encode-image', e.message); }
  finally    { restore(btn, orig); }
}

// ── DECODE IMAGE ───────────────────────────────────────────────────────────
async function decodeImage() {
  const btn  = document.querySelector('#tab-image .op-btn.gold');
  const orig = loading(btn);
  try {
    const stego = document.getElementById('stego-img-file').files[0];
    if (!stego) return err('result-decode-image', 'Select the stego image.');

    const fd = new FormData();
    fd.append('stego', stego);
    const d = await post('/api/decode-image', fd);
    if (d.error) return err('result-decode-image', d.error);

    ok('result-decode-image', [
      ['EXTRACTED SIZE', d.secret_size],
      ['OUTPUT',         d.file],
    ], d.file, true);
  } catch(e) { err('result-decode-image', e.message); }
  finally    { restore(btn, orig); }
}

// ── ENCODE FILE ────────────────────────────────────────────────────────────
async function encodeFile() {
  const btn  = document.querySelector('#tab-file .op-btn.teal');
  const orig = loading(btn);
  try {
    const cover  = document.getElementById('cover-file-img').files[0];
    const secret = document.getElementById('secret-file-input').files[0];
    if (!cover)  return err('result-encode-file', 'Select a cover image.');
    if (!secret) return err('result-encode-file', 'Select the file to hide.');

    const fd = new FormData();
    fd.append('cover', cover); fd.append('secret', secret);
    const d = await post('/api/encode-file', fd);
    if (d.error) return err('result-encode-file', d.error);

    ok('result-encode-file', [
      ['HIDDEN FILE',    d.filename],
      ['FILE SIZE',      fmtBytes(d.file_size)],
      ['CAPACITY USED',  d.usage_pct + '%'],
      ['OUTPUT',         d.file],
    ], d.file);
  } catch(e) { err('result-encode-file', e.message); }
  finally    { restore(btn, orig); }
}

// ── DECODE FILE ────────────────────────────────────────────────────────────
async function decodeFile() {
  const btn  = document.querySelector('#tab-file .op-btn.gold');
  const orig = loading(btn);
  try {
    const stego = document.getElementById('stego-file-img').files[0];
    if (!stego) return err('result-decode-file', 'Select the stego image.');

    const fd = new FormData();
    fd.append('stego', stego);
    const d = await post('/api/decode-file', fd);
    if (d.error) return err('result-decode-file', d.error);

    ok('result-decode-file', [
      ['FILENAME',  d.filename],
      ['FILE SIZE', fmtBytes(d.file_size)],
    ], d.file, true);
  } catch(e) { err('result-decode-file', e.message); }
  finally    { restore(btn, orig); }
}

// ── KEY GENERATION ─────────────────────────────────────────────────────────
async function generateKeys() {
  const btn  = document.querySelector('#tab-keys .op-btn');
  const orig = loading(btn);
  try {
    const d = await post('/api/keygen', new FormData());
    if (d.error) return err('result-keygen', d.error);

    document.getElementById('result-keygen').innerHTML = `
      <div class="result-ok">
        <div class="result-title teal">◆ KEY PAIR FORGED</div>
        <div class="result-row"><span class="rl">ALGORITHM</span><span class="rv">RSA-2048 + AES-256-GCM</span></div>

        <div style="margin-top:1rem">
          <div style="font-size:.65rem;letter-spacing:.1em;color:var(--teal);margin-bottom:.3rem">◈ PUBLIC KEY — SHARE THIS</div>
          <div class="key-pem-box">${esc(d.public_pem)}</div>
          <a class="dl-btn" href="/download/${encodeURIComponent(d.public_key)}" download style="margin-top:.5rem">⬇ DOWNLOAD PUBLIC.PEM</a>
        </div>

        <div style="margin-top:1rem">
          <div style="font-size:.65rem;letter-spacing:.1em;color:var(--gold);margin-bottom:.3rem">⬡ PRIVATE KEY — KEEP SECRET</div>
          <div class="key-pem-box">${esc(d.private_pem)}</div>
          <a class="dl-btn" href="/download/${encodeURIComponent(d.private_key)}" download style="margin-top:.5rem;background:var(--gold-dim);color:var(--gold);border-color:rgba(240,180,41,0.3)">⬇ DOWNLOAD PRIVATE.PEM</a>
        </div>
      </div>`;
  } catch(e) { err('result-keygen', e.message); }
  finally    { restore(btn, orig); }
}