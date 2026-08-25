const API_BASE = 'https://feedbrain.onrender.com';

// ─── STATE ───────────────────────────────────────────────
let currentUser = null;
let currentToken = null;

// ─── INIT ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const stored = await getStorage(['user_id', 'email', 'token']);
  if (stored.user_id && stored.token) {
    currentUser = { id: stored.user_id, email: stored.email };
    currentToken = stored.token;
    showApp();
    loadLibrary();
  } else {
    showAuth();
  }
  setupEventListeners();
});

// ─── STORAGE HELPERS ──────────────────────────────────────
function getStorage(keys) {
  return new Promise(resolve => chrome.storage.local.get(keys, resolve));
}

function setStorage(data) {
  return new Promise(resolve => chrome.storage.local.set(data, resolve));
}

function clearStorage() {
  return new Promise(resolve => chrome.storage.local.clear(resolve));
}

// ─── AUTH ─────────────────────────────────────────────────
function showAuth() {
  document.getElementById('authScreen').style.display = 'flex';
  document.getElementById('appScreen').style.display = 'none';
}

function showApp() {
  document.getElementById('authScreen').style.display = 'none';
  document.getElementById('appScreen').style.display = 'flex';
  document.getElementById('userEmail').textContent = currentUser.email;
}

async function handleLogin() {
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  const errorEl = document.getElementById('authError');
  const successEl = document.getElementById('authSuccess');

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields';
    return;
  }

  errorEl.textContent = '';
  document.getElementById('loginBtn').textContent = 'Logging in...';

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (res.ok) {
      currentUser = { id: data.user_id, email: data.email };
      currentToken = data.access_token;
      await setStorage({
        user_id: data.user_id,
        email: data.email,
        token: data.access_token
      });
      showApp();
      loadLibrary();
    } else {
      errorEl.textContent = data.detail || 'Login failed';
    }
  } catch (e) {
    errorEl.textContent = 'Connection error. Try again.';
  }

  document.getElementById('loginBtn').textContent = 'Login';
}

async function handleSignup() {
  const email = document.getElementById('authEmail').value.trim();
  const password = document.getElementById('authPassword').value;
  const errorEl = document.getElementById('authError');
  const successEl = document.getElementById('authSuccess');

  if (!email || !password) {
    errorEl.textContent = 'Please fill in all fields';
    return;
  }

  if (password.length < 6) {
    errorEl.textContent = 'Password must be at least 6 characters';
    return;
  }

  errorEl.textContent = '';
  document.getElementById('signupBtn').textContent = 'Creating account...';

  try {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (res.ok) {
      successEl.textContent = '✅ Account created! Please login.';
      errorEl.textContent = '';
    } else {
      errorEl.textContent = data.detail || 'Signup failed';
    }
  } catch (e) {
    errorEl.textContent = 'Connection error. Try again.';
  }

  document.getElementById('signupBtn').textContent = 'Create Account';
}

async function handleLogout() {
  await clearStorage();
  currentUser = null;
  currentToken = null;
  showAuth();
}

// ─── SAVE ─────────────────────────────────────────────────
async function handleSave() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const saveBtn = document.getElementById('saveBtn');
  const processingMsg = document.getElementById('processingMsg');

  saveBtn.textContent = 'Saving...';
  saveBtn.disabled = true;
  processingMsg.style.display = 'block';

  try {
    const res = await fetch(`${API_BASE}/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: url,
        user_id: currentUser.id
      })
    });

    const data = await res.json();

    if (res.ok) {
      document.getElementById('urlInput').value = '';
      processingMsg.textContent = `✅ Saved! "${data.title}"`;
      setTimeout(() => {
        processingMsg.style.display = 'none';
        processingMsg.textContent = '⚡ Processing your save...';
      }, 3000);
      loadLibrary();
    } else {
      processingMsg.textContent = '❌ Failed to save. Try again.';
      setTimeout(() => { processingMsg.style.display = 'none'; }, 3000);
    }
  } catch (e) {
    processingMsg.textContent = '❌ Connection error.';
    setTimeout(() => { processingMsg.style.display = 'none'; }, 3000);
  }

  saveBtn.textContent = 'Save 🧠';
  saveBtn.disabled = false;
}

// ─── SAVE CURRENT TAB ─────────────────────────────────────
async function saveCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab && tab.url &&
      !tab.url.startsWith('chrome://') &&
      !tab.url.startsWith('chrome-extension://') &&
      !tab.url.startsWith('about:')) {
    document.getElementById('urlInput').value = tab.url;
  }
}

// ─── SEARCH ───────────────────────────────────────────────
async function handleSearch() {
  const query = document.getElementById('searchInput').value.trim();
  if (!query) return;

  const resultsEl = document.getElementById('searchResults');
  resultsEl.innerHTML = '<div class="loading">Searching your saves...</div>';

  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        user_id: currentUser.id,
        limit: 5
      })
    });

    const data = await res.json();

    if (data.results && data.results.length > 0) {
      resultsEl.innerHTML = `
        <div class="section-title">${data.total} result${data.total !== 1 ? 's' : ''} for "${query}"</div>
        ${data.results.map(save => renderCard(save, save.relevance_reason)).join('')}
      `;
    } else {
      resultsEl.innerHTML = `
        <div class="empty-state">
          <div class="emoji">🔍</div>
          <p>No saves found for "${query}"</p>
          <p style="font-size:12px; margin-top:8px">Try saving more content first</p>
        </div>
      `;
    }
  } catch (e) {
    resultsEl.innerHTML = '<div class="empty-state">❌ Search failed. Try again.</div>';
  }
}

// ─── LIBRARY ──────────────────────────────────────────────
async function loadLibrary() {
  const libraryEl = document.getElementById('libraryContent');
  libraryEl.innerHTML = '<div class="loading">Loading your saves...</div>';

  try {
    const res = await fetch(`${API_BASE}/saves?user_id=${currentUser.id}`);
    const data = await res.json();

    if (data.saves && data.saves.length > 0) {
      const grouped = groupBySourceType(data.saves);
      let html = '';

      for (const [type, saves] of Object.entries(grouped)) {
        const icon = sourceIcon(type);
        html += `<div class="section-title">${icon} ${type.toUpperCase()} (${saves.length})</div>`;
        html += saves.map(save => renderCard(save)).join('');
      }

      libraryEl.innerHTML = html;
    } else {
      libraryEl.innerHTML = `
        <div class="empty-state">
          <div class="emoji">📚</div>
          <p>No saves yet</p>
          <p style="font-size:12px; margin-top:8px">Paste a URL above to save your first link</p>
        </div>
      `;
    }
  } catch (e) {
    libraryEl.innerHTML = '<div class="empty-state">❌ Failed to load library.</div>';
  }
}

// ─── DIGEST ───────────────────────────────────────────────
async function loadDigest() {
  const digestEl = document.getElementById('digestContent');
  digestEl.innerHTML = '<div class="loading">Loading your digest...</div>';

  try {
    const res = await fetch(`${API_BASE}/digest?user_id=${currentUser.id}`);
    const data = await res.json();

    if (data.resurfaces && data.resurfaces.length > 0) {
      digestEl.innerHTML = data.resurfaces.map(item => `
        ${renderCard(item.save, item.reason)}
      `).join('');
    } else {
      digestEl.innerHTML = `
        <div class="empty-state">
          <div class="emoji">✨</div>
          <p>No resurfaces yet</p>
          <p style="font-size:12px; margin-top:8px">Save more content to get your daily digest</p>
        </div>
      `;
    }
  } catch (e) {
    digestEl.innerHTML = '<div class="empty-state">❌ Failed to load digest.</div>';
  }
}

// ─── RENDER CARD ──────────────────────────────────────────
function renderCard(save, relevanceReason = null) {
  const summary = Array.isArray(save.summary) ? save.summary : [];
  const tags = Array.isArray(save.tags) ? save.tags : [];
  const sourceType = save.source_type || 'other';

  return `
    <div class="save-card" id="card-${save.id}">
      <div class="card-header">
        <span class="source-badge badge-${sourceType}">${sourceType}</span>
        <span class="card-title">${save.title || 'Untitled'}</span>
        <button onclick="deleteSave('${save.id}')" style="background:none;border:none;color:#555;cursor:pointer;font-size:16px;margin-left:auto">🗑️</button>
      </div>
      ${relevanceReason ? `<div class="relevance">✓ ${relevanceReason}</div>` : ''}
      <ul class="card-summary">
        ${summary.map(bullet => `<li>${bullet}</li>`).join('')}
      </ul>
      <div class="card-tags">
        ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
      </div>
      <a href="${save.url}" target="_blank" class="card-link">View original →</a>
    </div>
  `;
}

async function deleteSave(saveId) {
  if (!confirm('Delete this save?')) return;
  
  try {
    const res = await fetch(`${API_BASE}/saves/${saveId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUser.id })
    });
    
    if (res.ok) {
      document.getElementById(`card-${saveId}`).remove();
    }
  } catch (e) {
    console.error('Delete failed:', e);
  }
}

// ─── HELPERS ──────────────────────────────────────────────
function groupBySourceType(saves) {
  return saves.reduce((groups, save) => {
    const type = save.source_type || 'other';
    if (!groups[type]) groups[type] = [];
    groups[type].push(save);
    return groups;
  }, {});
}

function sourceIcon(type) {
  const icons = {
    youtube: '🎥',
    article: '📄',
    pdf: '📁',
    tweet: '🐦',
    instagram: '📸',
    other: '🔗'
  };
  return icons[type] || '🔗';
}

// ─── TABS ─────────────────────────────────────────────────
function setupTabs() {
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const tabName = tab.dataset.tab;
      document.getElementById('searchTab').style.display = 'none';
      document.getElementById('libraryTab').style.display = 'none';
      document.getElementById('digestTab').style.display = 'none';
      document.getElementById(`${tabName}Tab`).style.display = 'block';

      if (tabName === 'library') loadLibrary();
      if (tabName === 'digest') loadDigest();
    });
  });
}

// ─── EVENT LISTENERS ──────────────────────────────────────
function setupEventListeners() {
  document.getElementById('loginBtn').addEventListener('click', handleLogin);
  document.getElementById('signupBtn').addEventListener('click', handleSignup);
  document.getElementById('logoutBtn').addEventListener('click', handleLogout);
  document.getElementById('saveBtn').addEventListener('click', handleSave);
  document.getElementById('searchBtn').addEventListener('click', handleSearch);

  document.getElementById('authEmail').addEventListener('keypress', e => {
    if (e.key === 'Enter') handleLogin();
  });

  document.getElementById('authPassword').addEventListener('keypress', e => {
    if (e.key === 'Enter') handleLogin();
  });

  document.getElementById('searchInput').addEventListener('keypress', e => {
    if (e.key === 'Enter') handleSearch();
  });

  document.getElementById('urlInput').addEventListener('keypress', e => {
    if (e.key === 'Enter') handleSave();
  });

  document.getElementById('themeToggle').addEventListener('click', () => {
    document.body.classList.toggle('light');
    const isDark = !document.body.classList.contains('light');
    document.getElementById('themeToggle').textContent = isDark ? '🌙' : '☀️';
    chrome.storage.local.set({ theme: isDark ? 'dark' : 'light' });
  });

  saveCurrentTab();
  setupTabs();
}