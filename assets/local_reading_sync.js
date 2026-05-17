(() => {
  const PREFIX = 'researchBriefings.v2.';
  const QUEUE_KEY_PREFIX = 'researchBriefings.localSync.queue.v1.';
  const LAST_SIGNATURES_KEY_PREFIX = 'researchBriefings.localSync.lastSignatures.v1.';
  const USER_KEY = 'researchBriefings.localSync.user.v1';
  const HANDLE_DB = 'researchBriefingsLocalSync';
  const HANDLE_STORE = 'handles';
  const HANDLE_KEY = 'syncRoot';
  const VALID_DECISIONS = new Set(['skip', 'queue', 'reading', 'pass', 'read', 'important']);

  let syncRootHandle = null;
  let briefingCache = null;
  let briefingsCache = null;
  let syncStatus = 'initializing';
  let lanAvailable = false;
  let suppressCapture = false;
  let currentUser = resolveUser();

  function sanitizeUser(value) {
    return String(value || '').replace(/[^A-Za-z0-9._-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '').slice(0, 48);
  }

  function resolveUser() {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = sanitizeUser(params.get('user') || '');
    if (fromUrl && fromUrl !== 'ziang') {
      localStorage.setItem(USER_KEY, fromUrl);
      return fromUrl;
    }
    const explicitZiang = params.has('user') && sanitizeUser(params.get('user')) === 'ziang';
    if (explicitZiang) {
      localStorage.setItem(USER_KEY, 'ziang');
      return 'ziang';
    }
    return sanitizeUser(localStorage.getItem(USER_KEY) || 'ziang');
  }

  function apiPath(path) {
    return `${path}?user=${encodeURIComponent(currentUser)}`;
  }

  function queueKey() {
    return `${QUEUE_KEY_PREFIX}${currentUser || 'anonymous'}`;
  }

  function lastSignaturesKey() {
    return `${LAST_SIGNATURES_KEY_PREFIX}${currentUser || 'anonymous'}`;
  }

  function setCurrentUser(value) {
    const next = sanitizeUser(value);
    if (!next) {
      setStatus('enter user id first');
      return;
    }
    localStorage.setItem(USER_KEY, next);
    const url = new URL(window.location.href);
    url.searchParams.set('user', next);
    window.location.href = url.toString();
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(HANDLE_DB, 1);
      request.onupgradeneeded = () => request.result.createObjectStore(HANDLE_STORE);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async function saveHandle(handle) {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(HANDLE_STORE, 'readwrite');
      tx.objectStore(HANDLE_STORE).put(handle, HANDLE_KEY);
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
  }

  async function loadHandle() {
    try {
      const db = await openDb();
      return await new Promise((resolve, reject) => {
        const tx = db.transaction(HANDLE_STORE, 'readonly');
        const request = tx.objectStore(HANDLE_STORE).get(HANDLE_KEY);
        request.onsuccess = () => resolve(request.result || null);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      return null;
    }
  }

  async function verifyHandle(handle, write = false) {
    if (!handle || !handle.queryPermission) return false;
    const options = { mode: write ? 'readwrite' : 'read' };
    if ((await handle.queryPermission(options)) === 'granted') return true;
    return (await handle.requestPermission(options)) === 'granted';
  }

  function readQueue() {
    try { return JSON.parse(localStorage.getItem(queueKey()) || '[]'); }
    catch (error) { return []; }
  }

  function writeQueue(events) {
    localStorage.setItem(queueKey(), JSON.stringify(events.slice(-500)));
    updatePanel();
  }

  function readLastSignatures() {
    try { return JSON.parse(localStorage.getItem(lastSignaturesKey()) || '{}'); }
    catch (error) { return {}; }
  }

  function writeLastSignatures(signatures) {
    localStorage.setItem(lastSignaturesKey(), JSON.stringify(signatures));
  }

  function setStatus(value) {
    syncStatus = value;
    updatePanel();
  }

  function extractJsonAfterMarker(source, marker, terminator) {
    const start = source.indexOf(marker);
    if (start < 0) return null;
    const from = start + marker.length;
    const end = source.indexOf(terminator, from);
    if (end < 0) return null;
    return source.slice(from, end).trim();
  }

  function extractBriefing() {
    if (briefingCache) return briefingCache;
    const scripts = [...document.scripts].map(script => script.textContent || '').join('\n');
    const raw = extractJsonAfterMarker(scripts, 'const BRIEFING = ', ';\n  const PROJECTS =');
    if (!raw) return null;
    try {
      briefingCache = JSON.parse(raw);
      return briefingCache;
    } catch (error) {
      return null;
    }
  }

  function extractBriefings() {
    if (briefingsCache) return briefingsCache;
    const one = extractBriefing();
    if (one) {
      briefingsCache = [one];
      return briefingsCache;
    }
    const scripts = [...document.scripts].map(script => script.textContent || '').join('\n');
    const raw = extractJsonAfterMarker(scripts, 'const BRIEFINGS = ', ';\n  const PROJECTS =');
    if (!raw) return [];
    try {
      briefingsCache = JSON.parse(raw);
      return briefingsCache;
    } catch (error) {
      return [];
    }
  }

  function findPaper(paperId) {
    for (const briefing of extractBriefings()) {
      const paper = (briefing.papers || []).find(item => item.id === paperId);
      if (paper) return { briefing, paper };
    }
    return null;
  }

  function sanitizeName(value) {
    return String(value).replace(/[^A-Za-z0-9._-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '').slice(0, 80) || 'event';
  }

  function shortHash(value) {
    let hash = 2166136261;
    const text = String(value);
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16).padStart(8, '0');
  }

  function eventFileName(event) {
    const stamp = event.createdAt.replace(/[:.]/g, '-');
    return `${stamp}__${shortHash(event.paperId)}__${sanitizeName(event.paperId)}__${event.decision}.json`;
  }

  function stateSignature(event) {
    return [
      event.paperId || '',
      event.decision || '',
      event.shareUrl || '',
      event.conversationUrl || '',
      event.userNote || ''
    ].join('\u001f');
  }

  function effectiveSignature(paperId, queue, lastSignatures) {
    for (let index = queue.length - 1; index >= 0; index -= 1) {
      if (queue[index].paperId === paperId) return stateSignature(queue[index]);
    }
    return lastSignatures[paperId] || '';
  }

  function rememberWritten(event) {
    const last = readLastSignatures();
    last[event.paperId] = stateSignature(event);
    writeLastSignatures(last);
  }

  function buildEventFromState(briefing, paper, state, source = 'lan-web') {
    if (!currentUser) return null;
    const decision = state.decision || 'open';
    if (!VALID_DECISIONS.has(decision)) return null;
    const createdAt = new Date().toISOString();
    return {
      schemaVersion: 1,
      eventId: `${createdAt}__${paper.id}`,
      briefingSlug: briefing.slug,
      briefingDate: briefing.date,
      paperId: paper.id,
      paperTitle: paper.title,
      paperUrl: paper.url,
      section: paper.section,
      topic: briefing.topic,
      decision,
      shareUrl: state.shareUrl || '',
      conversationUrl: state.conversationUrl || '',
      userNote: state.userNote || '',
      createdAt,
      source,
      userId: currentUser
    };
  }

  function buildEvent(key, rawValue) {
    const paperId = key.slice(PREFIX.length);
    const found = findPaper(paperId);
    if (!found) return null;
    let state;
    try { state = JSON.parse(rawValue); }
    catch (error) { return null; }
    return buildEventFromState(found.briefing, found.paper, state, 'lan-web');
  }

  function readPaperState(paperId) {
    try { return JSON.parse(localStorage.getItem(`${PREFIX}${paperId}`) || '{}'); }
    catch (error) { return {}; }
  }

  function remoteIsNewer(remote, local) {
    if (!local || !local.updatedAt) return true;
    if (!remote.updatedAt) return false;
    return String(remote.updatedAt) > String(local.updatedAt);
  }

  async function hydrateFromPublicSummary() {
    if (!currentUser) return 0;
    if (!window.fetch || window.location.protocol === 'file:') return 0;
    try {
      const response = await fetch(apiPath('/api/public-reading-summary'), { cache: 'no-store' });
      if (!response.ok) return 0;
      const summary = await response.json();
      const papers = Array.isArray(summary.papers) ? summary.papers : [];
      let changed = 0;
      suppressCapture = true;
      for (const paper of papers) {
        if (!paper.paperId || !paper.decision || paper.decision === 'open') continue;
        const key = `${PREFIX}${paper.paperId}`;
        const local = readPaperState(paper.paperId);
        if (!remoteIsNewer(paper, local)) continue;
        localStorage.setItem(key, JSON.stringify({
          ...local,
          decision: paper.decision,
          star: paper.decision === 'important',
          updatedAt: paper.updatedAt || new Date().toISOString(),
          transcriptStatus: paper.transcriptStatus || local.transcriptStatus || ''
        }));
        changed += 1;
      }
      suppressCapture = false;
      if (changed) {
        setStatus(`hydrated ${changed} records from host`);
        const flag = `researchBriefings.localSync.hydrated.${summary.generatedAt || 'latest'}`;
        if (!sessionStorage.getItem(flag)) {
          sessionStorage.setItem(flag, '1');
          window.setTimeout(() => window.location.reload(), 250);
        }
      }
      return changed;
    } catch (error) {
      suppressCapture = false;
      return 0;
    }
  }

  async function postLanEvent(event) {
    if (!currentUser) {
      setStatus('enter user id first');
      return false;
    }
    if (!window.fetch || window.location.protocol === 'file:') return false;
    try {
      const response = await fetch('/api/reading-event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ schemaVersion: 1, user: currentUser, event })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      lanAvailable = true;
      rememberWritten(event);
      setStatus('LAN write ok');
      return true;
    } catch (error) {
      lanAvailable = false;
      return false;
    }
  }

  async function checkLan() {
    if (!currentUser) {
      lanAvailable = false;
      setStatus('enter user id first');
      return false;
    }
    if (!window.fetch || window.location.protocol === 'file:') {
      lanAvailable = false;
      setStatus('file fallback mode');
      return false;
    }
    try {
      const response = await fetch(apiPath('/api/health'), { cache: 'no-store' });
      lanAvailable = response.ok;
      setStatus(lanAvailable ? 'LAN connected' : 'LAN unavailable');
      return lanAvailable;
    } catch (error) {
      lanAvailable = false;
      setStatus('LAN unavailable');
      return false;
    }
  }

  async function ensurePendingDir() {
    if (!syncRootHandle) return null;
    const inbox = await syncRootHandle.getDirectoryHandle('inbox', { create: true });
    return await inbox.getDirectoryHandle('pending', { create: true });
  }

  async function writeEventFile(event) {
    const pending = await ensurePendingDir();
    if (!pending) throw new Error('missing sync root');
    const file = await pending.getFileHandle(eventFileName(event), { create: true });
    const writable = await file.createWritable();
    await writable.write(JSON.stringify(event, null, 2));
    await writable.close();
    rememberWritten(event);
  }

  async function flushQueue() {
    if (!currentUser) {
      setStatus('enter user id first');
      return;
    }
    const queue = readQueue();
    if (!queue.length) {
      if (lanAvailable) setStatus('LAN connected, no pending events');
      updatePanel();
      return;
    }

    const failedLan = [];
    for (const event of queue) {
      if (!(await postLanEvent(event))) failedLan.push(event);
    }
    if (!failedLan.length) {
      writeQueue([]);
      setStatus('queued events sent to LAN');
      return;
    }

    if (!syncRootHandle) syncRootHandle = await loadHandle();
    if (!syncRootHandle) {
      writeQueue(failedLan);
      setStatus(`LAN failed; ${failedLan.length} queued locally`);
      return;
    }
    if (!(await verifyHandle(syncRootHandle, true))) {
      writeQueue(failedLan);
      setStatus('fallback directory has no write permission');
      return;
    }

    const failedFile = [];
    for (const event of failedLan) {
      try { await writeEventFile(event); }
      catch (error) { failedFile.push(event); }
    }
    writeQueue(failedFile);
    setStatus(failedFile.length ? `fallback partly failed: ${failedFile.length}` : 'written to fallback pending');
  }

  async function enqueue(event) {
    if (!currentUser) {
      setStatus('enter user id first');
      return;
    }
    const queue = readQueue();
    const signature = stateSignature(event);
    const lastSignatures = readLastSignatures();
    if (effectiveSignature(event.paperId, queue, lastSignatures) === signature) {
      setStatus('duplicate event skipped');
      return;
    }
    if (await postLanEvent(event)) {
      await flushQueue();
      return;
    }
    writeQueue(queue.concat([event]).slice(-500));
    setStatus('LAN failed; event queued');
    await flushQueue();
  }

  function shouldBackfill(state) {
    if (!state) return false;
    if (state.decision && state.decision !== 'open') return true;
    return Boolean(state.shareUrl || state.userNote);
  }

  async function backfillExisting() {
    if (!currentUser) {
      setStatus('enter user id first');
      return;
    }
    const events = [];
    for (const briefing of extractBriefings()) {
      for (const paper of briefing.papers || []) {
        const raw = localStorage.getItem(`${PREFIX}${paper.id}`);
        if (!raw) continue;
        let state;
        try { state = JSON.parse(raw); }
        catch (error) { continue; }
        if (!shouldBackfill(state)) continue;
        const event = buildEventFromState(briefing, paper, state, 'lan-web-backfill');
        if (event) events.push(event);
      }
    }
    if (!events.length) {
      setStatus('no existing records to backfill');
      return;
    }
    const queue = readQueue();
    const lastSignatures = readLastSignatures();
    const additions = events.filter(event => effectiveSignature(event.paperId, queue, lastSignatures) !== stateSignature(event));
    if (!additions.length) {
      setStatus('existing records already queued or written');
      return;
    }
    writeQueue(queue.concat(additions).slice(-500));
    setStatus(`backfilled ${additions.length} records`);
    await flushQueue();
  }

  const nativeSetItem = Storage.prototype.setItem;
  Storage.prototype.setItem = function patchedSetItem(key, value) {
    nativeSetItem.call(this, key, value);
    if (suppressCapture) return;
    if (this === localStorage && typeof key === 'string' && key.startsWith(PREFIX)) {
      const event = buildEvent(key, value);
      if (event) enqueue(event);
    }
  };

  async function chooseRoot() {
    if (!window.showDirectoryPicker) {
      setStatus('browser does not support directory fallback');
      return;
    }
    try {
      syncRootHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
      await saveHandle(syncRootHandle);
      setStatus('fallback directory selected');
      await flushQueue();
      await backfillExisting();
    } catch (error) {
      setStatus(`directory selection failed: ${error.name || 'error'}`);
    }
  }

  function downloadQueue() {
    const queue = readQueue();
    const blob = new Blob([JSON.stringify(queue, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `reading-events-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function updatePanel() {
    const panel = document.querySelector('.rb-local-sync-panel');
    if (!panel) return;
    const count = readQueue().length;
    const state = !currentUser ? 'idle' : count > 0 ? 'pending' : lanAvailable ? 'synced' : 'offline';
    const label = !currentUser ? 'choose user' : count > 0 ? `${count} pending` : lanAvailable ? 'synced' : 'offline';
    panel.dataset.lan = lanAvailable ? 'on' : 'off';
    panel.dataset.syncState = state;
    panel.querySelector('[data-local-sync-count]').textContent = String(count);
    panel.querySelector('[data-local-sync-status]').textContent = syncStatus;
    panel.querySelectorAll('[data-local-sync-user-label]').forEach(item => { item.textContent = currentUser || 'no user'; });
    panel.querySelector('[data-local-sync-pill-status]').textContent = label;
    const userInput = panel.querySelector('[data-local-sync-user]');
    if (userInput && userInput.value !== (currentUser || '')) userInput.value = currentUser || '';
  }

  function mountPanel() {
    if (document.querySelector('.rb-local-sync-panel')) return;
    const panel = document.createElement('div');
    panel.className = 'rb-local-sync-panel';
    panel.innerHTML = `
      <style>
        .rb-local-sync-panel{position:fixed;left:18px;bottom:18px;z-index:9999;font:12px/1.35 "Microsoft YaHei","Segoe UI",sans-serif;color:#102b32}
        .rb-local-sync-toggle{display:flex;align-items:center;gap:8px;border:1px solid rgba(17,116,137,.28);background:rgba(250,254,255,.94);backdrop-filter:blur(12px);border-radius:999px;padding:8px 11px;box-shadow:0 10px 30px rgba(22,72,84,.16);color:#102b32;cursor:pointer}
        .rb-local-sync-dot{width:8px;height:8px;border-radius:999px;background:#98aab0;box-shadow:0 0 0 3px rgba(152,170,176,.16)}
        .rb-local-sync-panel[data-sync-state="synced"] .rb-local-sync-dot{background:#20a66a;box-shadow:0 0 0 3px rgba(32,166,106,.14)}
        .rb-local-sync-panel[data-sync-state="pending"] .rb-local-sync-dot{background:#d99a13;box-shadow:0 0 0 3px rgba(217,154,19,.17)}
        .rb-local-sync-panel[data-sync-state="offline"] .rb-local-sync-dot{background:#c95f54;box-shadow:0 0 0 3px rgba(201,95,84,.16)}
        .rb-local-sync-panel[data-sync-state="idle"] .rb-local-sync-dot{background:#8da0a6;box-shadow:0 0 0 3px rgba(141,160,166,.16)}
        .rb-local-sync-user-pill{font-weight:800;letter-spacing:.02em}
        .rb-local-sync-pill-status{color:#5d747a;font-weight:700}
        .rb-local-sync-card{display:none;position:absolute;left:0;bottom:44px;width:min(320px,calc(100vw - 28px));background:rgba(250,254,255,.97);border:1px solid rgba(17,116,137,.22);border-radius:14px;box-shadow:0 18px 46px rgba(22,72,84,.2);padding:12px}
        .rb-local-sync-panel[data-open="true"] .rb-local-sync-card{display:block}
        .rb-local-sync-head{display:flex;justify-content:space-between;gap:10px;align-items:flex-start;margin-bottom:10px}
        .rb-local-sync-title{font-weight:900;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:#006f86}
        .rb-local-sync-status{color:#60777e;margin-top:2px;word-break:break-word}
        .rb-local-sync-user-row{display:flex;gap:7px;margin:8px 0}
        .rb-local-sync-user-row input{min-width:0;flex:1;border:1px solid rgba(0,137,167,.25);border-radius:9px;padding:7px 9px;color:#12323a;background:#fff}
        .rb-local-sync-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px}
        .rb-local-sync-actions button,.rb-local-sync-login{border:1px solid rgba(0,137,167,.28);background:#fff;color:#006f86;border-radius:9px;padding:7px 9px;cursor:pointer;font-weight:700}
        .rb-local-sync-actions button:first-child{background:#007f98;color:#fff;border-color:#007f98}
        .rb-local-sync-meta{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:8px}
        .rb-local-sync-meta div{border:1px solid rgba(0,137,167,.16);border-radius:9px;padding:7px;background:#f5fbfc}
        .rb-local-sync-meta span{display:block;color:#71878d;font-size:11px}
        .rb-local-sync-tools{margin-top:9px;border-top:1px solid rgba(0,137,167,.16);padding-top:8px}
        .rb-local-sync-tools summary{cursor:pointer;color:#60777e;font-weight:700}
        .rb-local-sync-tools .rb-local-sync-actions{margin-top:7px}
      </style>
      <button class="rb-local-sync-toggle" data-local-sync-toggle type="button" aria-expanded="false">
        <span class="rb-local-sync-dot" aria-hidden="true"></span>
        <span class="rb-local-sync-user-pill" data-local-sync-user-label>${currentUser || 'no user'}</span>
        <span class="rb-local-sync-pill-status" data-local-sync-pill-status>initializing</span>
      </button>
      <div class="rb-local-sync-card">
      <div class="rb-local-sync-head">
        <div>
          <div class="rb-local-sync-title">Reading Sync</div>
          <div class="rb-local-sync-status" data-local-sync-status>initializing</div>
        </div>
      </div>
      <div class="rb-local-sync-user-row">
        <input data-local-sync-user placeholder="user id" value="${currentUser || ''}" />
        <button class="rb-local-sync-login" data-local-sync-login>${currentUser ? 'switch' : 'login'}</button>
      </div>
      <div class="rb-local-sync-meta">
        <div><span>User</span><strong data-local-sync-user-label>${currentUser || 'no user'}</strong></div>
        <div><span>Pending</span><strong data-local-sync-count>0</strong></div>
      </div>
      <div class="rb-local-sync-actions">
        <button data-local-sync-flush>sync now</button>
        <button data-local-sync-backfill>backfill</button>
      </div>
      <details class="rb-local-sync-tools">
        <summary>diagnostics</summary>
        <div class="rb-local-sync-actions">
          <button data-local-sync-root>fallback folder</button>
          <button data-local-sync-download>download events</button>
        </div>
      </details>
      </div>`;
    document.body.appendChild(panel);
    const userInput = panel.querySelector('[data-local-sync-user]');
    const toggle = panel.querySelector('[data-local-sync-toggle]');
    toggle.addEventListener('click', () => {
      const open = panel.dataset.open !== 'true';
      panel.dataset.open = open ? 'true' : 'false';
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    panel.querySelector('[data-local-sync-login]').addEventListener('click', () => setCurrentUser(userInput.value));
    userInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') setCurrentUser(userInput.value);
    });
    panel.querySelector('[data-local-sync-root]').addEventListener('click', chooseRoot);
    panel.querySelector('[data-local-sync-flush]').addEventListener('click', flushQueue);
    panel.querySelector('[data-local-sync-backfill]').addEventListener('click', backfillExisting);
    panel.querySelector('[data-local-sync-download]').addEventListener('click', downloadQueue);
    updatePanel();
    loadHandle().then(handle => {
      syncRootHandle = handle;
      return checkLan();
    }).then(() => hydrateFromPublicSummary()).then(() => flushQueue());
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mountPanel);
  else mountPanel();
})();
