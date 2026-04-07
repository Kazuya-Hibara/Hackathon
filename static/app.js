// ===== TOAST NOTIFICATIONS =====
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: 'check-circle', error: 'alert-circle', info: 'info' };
  toast.innerHTML = `<i data-lucide="${icons[type] || 'info'}" style="width:18px;height:18px;flex-shrink:0"></i><span>${message}</span>`;
  container.appendChild(toast);
  if (typeof lucide !== 'undefined') lucide.createIcons({ nodes: [toast] });
  setTimeout(() => {
    toast.classList.add('toast-exit');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

// ===== SKELETON LOADER =====
function showSkeletons(el, count = 3) {
  el.innerHTML = Array.from({ length: count }, () =>
    '<div class="skeleton skeleton-card"></div>'
  ).join('');
}

// ===== STATE =====
let currentDate = new Date().toISOString().split('T')[0];

// ===== API HELPERS =====
async function api(path, opts = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// ===== DATE NAVIGATION =====
function formatDate(d) {
  const opts = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
  return new Date(d + 'T12:00:00').toLocaleDateString('en-US', opts);
}

function changeDate(delta) {
  const d = new Date(currentDate + 'T12:00:00');
  d.setDate(d.getDate() + delta);
  currentDate = d.toISOString().split('T')[0];
  refresh();
}

function goToday() {
  currentDate = new Date().toISOString().split('T')[0];
  refresh();
}

// ===== TAB SWITCHING =====
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(p => p.style.display = 'none');
    const target = document.getElementById('tab-' + tab.dataset.tab);
    target.style.display = '';
    // Re-trigger animation
    target.style.animation = 'none';
    target.offsetHeight; // force reflow
    target.style.animation = '';
    // Load tab-specific data
    if (tab.dataset.tab === 'growth') loadGrowthDashboard();
    if (tab.dataset.tab === 'archive') loadArchive();
    if (typeof lucide !== 'undefined') lucide.createIcons();
  });
});

// ===== ENTRIES =====
async function loadEntries() {
  const el = document.getElementById('entries-list');
  showSkeletons(el);
  try {
    const entries = await api(`/entries?date=${currentDate}`);
    if (!entries.length) {
      el.innerHTML = `<div class="empty-state">
        <i data-lucide="clipboard-list" class="empty-icon"></i>
        <h3>No impact items yet</h3>
        <p>Log your first impact item to start tracking your day.</p>
      </div>`;
      if (typeof lucide !== 'undefined') lucide.createIcons();
      return;
    }
    el.innerHTML = entries.map(e => `
      <div class="card">
        <div class="card-header">
          <div>
            <span class="badge badge-category">${e.category}</span>
            <span class="badge badge-impact-${e.impact_level || 'MEDIUM'}">${e.impact_level || '-'}</span>
            ${e.scope_tag ? `<span class="badge badge-scope">${e.scope_tag}</span>` : ''}
          </div>
          <button class="btn btn-dismiss" onclick="deleteEntry(${e.id})" title="Delete">
            <i data-lucide="trash-2" style="width:14px;height:14px"></i>
          </button>
        </div>
        <p style="font-size:.9rem;line-height:1.5">${e.description}</p>
        <div class="entry-meta">
          ${e.time_estimate ? `<span><i data-lucide="clock" style="width:12px;height:12px;vertical-align:middle"></i> ${e.time_estimate}</span>` : ''}
          ${e.stakeholders?.length ? `<span><i data-lucide="users" style="width:12px;height:12px;vertical-align:middle"></i> ${e.stakeholders.join(', ')}</span>` : ''}
          ${e.source === 'suggestion' ? '<span><i data-lucide="sparkles" style="width:12px;height:12px;vertical-align:middle"></i> AI suggested</span>' : ''}
        </div>
        ${e.reasoning ? `<div class="reasoning">${e.reasoning}</div>` : ''}
      </div>
    `).join('');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch (err) {
    el.innerHTML = `<div class="empty">Error loading entries: ${err.message}</div>`;
  }
}

async function deleteEntry(id) {
  await api(`/entries/${id}`, { method: 'DELETE' });
  showToast('Entry deleted', 'info');
  loadEntries();
}

// ===== SUGGESTIONS =====
async function loadSuggestions() {
  const el = document.getElementById('suggestions-list');
  showSkeletons(el);
  try {
    const suggestions = await api(`/suggestions?status=pending&date=${currentDate}`);
    if (!suggestions.length) {
      el.innerHTML = `<div class="empty-state">
        <i data-lucide="sparkles" class="empty-icon"></i>
        <h3>No pending suggestions</h3>
        <p>Click Generate to let AI analyze your day.</p>
      </div>`;
      if (typeof lucide !== 'undefined') lucide.createIcons();
      return;
    }
    el.innerHTML = suggestions.map(s => `
      <div class="card suggestion-card">
        <div class="card-header">
          <div>
            <span class="badge badge-category">${s.suggested_category}</span>
            <span class="badge badge-impact-${s.suggested_impact_level || 'MEDIUM'}">${s.suggested_impact_level || '-'}</span>
            ${s.suggested_scope_tag ? `<span class="badge badge-scope">${s.suggested_scope_tag}</span>` : ''}
          </div>
          <span style="font-size:.72rem;color:var(--muted);font-weight:500">${Math.round((s.confidence || 0) * 100)}% confidence</span>
        </div>
        <p style="font-size:.9rem;line-height:1.5">${s.suggested_description}</p>
        ${s.reasoning ? `<div class="reasoning">${s.reasoning}</div>` : ''}
        <div class="suggestion-actions">
          <button class="btn btn-accept" onclick="acceptSuggestion(${s.id})"><i data-lucide="check" style="width:14px;height:14px"></i> Accept</button>
          <button class="btn btn-dismiss" onclick="dismissSuggestion(${s.id})"><i data-lucide="x" style="width:14px;height:14px"></i> Dismiss</button>
        </div>
      </div>
    `).join('');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch (err) {
    el.innerHTML = `<div class="empty">Error: ${err.message}</div>`;
  }
}

async function generateSuggestions() {
  const el = document.getElementById('suggestions-list');
  showSkeletons(el, 4);
  try {
    const result = await api(`/suggestions/generate?date=${currentDate}`, { method: 'POST' });
    showToast(`Generated ${result.count} suggestions`, 'success');
    loadSuggestions();
  } catch (err) {
    el.innerHTML = `<div class="empty">Generation failed: ${err.message}</div>`;
    showToast('Suggestion generation failed', 'error');
  }
}

async function acceptSuggestion(id) {
  await api(`/suggestions/${id}/accept`, { method: 'POST' });
  showToast('Suggestion accepted!', 'success');
  loadSuggestions();
  loadEntries();
}

async function dismissSuggestion(id) {
  await api(`/suggestions/${id}/dismiss`, { method: 'POST' });
  showToast('Suggestion dismissed', 'info');
  loadSuggestions();
}

// ===== ENTRY FORM =====
function toggleForm() {
  const form = document.getElementById('entry-form');
  if (form.style.display === 'none') {
    form.style.display = '';
    form.style.animation = 'none';
    form.offsetHeight;
    form.style.animation = 'slideDown 0.35s ease-out';
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } else {
    form.style.display = 'none';
  }
}

async function submitEntry() {
  const entry = {
    date: currentDate,
    category: document.getElementById('f-category').value,
    description: document.getElementById('f-description').value,
    impact_level: document.getElementById('f-impact').value,
    time_estimate: document.getElementById('f-time').value || null,
    scope_tag: document.getElementById('f-scope').value,
  };
  if (!entry.description) {
    showToast('Description is required', 'error');
    return;
  }
  await api('/entries', { method: 'POST', body: JSON.stringify(entry) });
  document.getElementById('f-description').value = '';
  document.getElementById('f-time').value = '';
  toggleForm();
  showToast('Impact item saved!', 'success');
  loadEntries();
}

// ===== DAY SUMMARY =====
async function loadDayMeta() {
  try {
    const meta = await api(`/daily-meta/${currentDate}`);
    document.getElementById('ds-load').value = meta.cognitive_load || '';
    document.getElementById('ds-energy').value = meta.energy || '';
  } catch { /* ignore */ }
}

async function saveDayMeta() {
  await api(`/daily-meta/${currentDate}`, {
    method: 'PUT',
    body: JSON.stringify({
      cognitive_load: document.getElementById('ds-load').value || null,
      energy: document.getElementById('ds-energy').value || null,
    }),
  });
  showToast('Day summary saved', 'success');
}

// ===== CONNECTORS =====
async function loadConnectors() {
  const el = document.getElementById('connectors-list');
  try {
    const connectors = await api('/connectors');
    el.innerHTML = connectors.map(c => `
      <div class="connector">
        <div class="dot ${c.last_sync ? 'dot-active' : 'dot-inactive'}"></div>
        ${c.connector_id}
      </div>
    `).join('');
  } catch {
    el.innerHTML = '<span style="color:var(--muted);font-size:.8rem">DB not connected</span>';
  }
}

async function syncAll() {
  const connectors = ['bright_data'];
  for (const c of connectors) {
    try {
      await api(`/connectors/${c}/sync`, { method: 'POST', body: '{}' });
    } catch { /* skip unavailable */ }
  }
  loadConnectors();
  showToast('Sync complete', 'success');
}

// ===== GROWTH DASHBOARD =====
let chartInstances = {};

async function loadGrowthDashboard() {
  const range = parseInt(document.getElementById('growth-range').value);
  const dateTo = new Date();
  const dateFrom = new Date();
  dateFrom.setDate(dateFrom.getDate() - range);

  const fmt = d => d.toISOString().split('T')[0];

  try {
    const entries = await api(`/entries?date_from=${fmt(dateFrom)}&date_to=${fmt(dateTo)}`);

    // Stats
    const total = entries.length;
    const high = entries.filter(e => e.impact_level === 'HIGH').length;
    const aiSuggested = entries.filter(e => e.source === 'suggestion').length;
    const categories = new Set(entries.map(e => e.category)).size;

    animateNumber('stat-total', total);
    animateNumber('stat-high', high);
    animateNumber('stat-suggestions', aiSuggested);
    animateNumber('stat-categories', categories);

    // Category distribution (donut)
    const catCounts = {};
    entries.forEach(e => { catCounts[e.category] = (catCounts[e.category] || 0) + 1; });
    const catColors = ['#3b82f6', '#8b5cf6', '#22c55e', '#eab308', '#ef4444', '#ec4899', '#06b6d4'];
    renderChart('chart-categories', 'doughnut', {
      labels: Object.keys(catCounts),
      datasets: [{
        data: Object.values(catCounts),
        backgroundColor: catColors.slice(0, Object.keys(catCounts).length),
        borderWidth: 0,
        hoverOffset: 8,
      }]
    }, { cutout: '65%' });

    // Impact level (bar)
    const impactCounts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
    entries.forEach(e => { if (e.impact_level) impactCounts[e.impact_level]++; });
    renderChart('chart-impact', 'bar', {
      labels: Object.keys(impactCounts),
      datasets: [{
        label: 'Count',
        data: Object.values(impactCounts),
        backgroundColor: ['rgba(239,68,68,0.7)', 'rgba(234,179,8,0.7)', 'rgba(148,163,184,0.5)'],
        borderRadius: 8,
        borderSkipped: false,
      }]
    });

    // Daily trend (line)
    const dailyCounts = {};
    for (let d = new Date(dateFrom); d <= dateTo; d.setDate(d.getDate() + 1)) {
      dailyCounts[fmt(new Date(d))] = 0;
    }
    entries.forEach(e => {
      const dateStr = typeof e.date === 'string' ? e.date : e.date;
      if (dailyCounts[dateStr] !== undefined) dailyCounts[dateStr]++;
    });
    renderChart('chart-trend', 'line', {
      labels: Object.keys(dailyCounts).map(d => d.slice(5)),
      datasets: [{
        label: 'Items',
        data: Object.values(dailyCounts),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59,130,246,0.08)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#0a0f1e',
        pointBorderWidth: 2,
      }]
    });

  } catch (err) {
    showToast('Failed to load growth data: ' + err.message, 'error');
  }
}

function renderChart(canvasId, type, data, extraOpts = {}) {
  if (chartInstances[canvasId]) chartInstances[canvasId].destroy();
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const isDoughnut = type === 'doughnut';
  chartInstances[canvasId] = new Chart(ctx, {
    type,
    data,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 800, easing: 'easeOutQuart' },
      plugins: {
        legend: {
          display: isDoughnut,
          position: 'bottom',
          labels: { color: '#94a3b8', padding: 16, usePointStyle: true, pointStyleWidth: 10, font: { size: 11 } }
        },
      },
      scales: !isDoughnut ? {
        x: {
          ticks: { color: '#64748b', font: { size: 10 } },
          grid: { color: 'rgba(255,255,255,0.04)' },
          border: { color: 'rgba(255,255,255,0.06)' },
        },
        y: {
          ticks: { color: '#64748b', font: { size: 10 }, stepSize: 1 },
          grid: { color: 'rgba(255,255,255,0.04)' },
          border: { color: 'rgba(255,255,255,0.06)' },
          beginAtZero: true,
        }
      } : undefined,
      ...extraOpts,
    }
  });
}

function animateNumber(elId, target) {
  const el = document.getElementById(elId);
  if (!el) return;
  const start = parseInt(el.textContent) || 0;
  if (start === target) { el.textContent = target; return; }
  const duration = 600;
  const startTime = performance.now();
  function step(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// Growth range listener
document.getElementById('growth-range')?.addEventListener('change', loadGrowthDashboard);

// ===== ARCHIVE =====
async function loadArchive() {
  const el = document.getElementById('archive-list');
  const emptyEl = document.getElementById('archive-empty');
  showSkeletons(el, 2);
  try {
    const entries = await api('/entries?include_deleted=true');
    const deleted = entries.filter(e => e.deleted);
    if (!deleted.length) {
      el.innerHTML = '';
      if (emptyEl) emptyEl.style.display = '';
      return;
    }
    if (emptyEl) emptyEl.style.display = 'none';
    el.innerHTML = deleted.map(e => `
      <div class="card">
        <div class="card-header">
          <div><span class="badge badge-category">${e.category}</span></div>
          <button class="btn btn-primary" onclick="restoreEntry(${e.id})">
            <i data-lucide="undo-2" style="width:14px;height:14px"></i> Restore
          </button>
        </div>
        <p style="font-size:.9rem;opacity:0.7;line-height:1.5">${e.description}</p>
      </div>
    `).join('');
    if (typeof lucide !== 'undefined') lucide.createIcons();
  } catch (err) {
    el.innerHTML = `<div class="empty">Error: ${err.message}</div>`;
  }
}

async function restoreEntry(id) {
  await api(`/entries/${id}/restore`, { method: 'POST' });
  showToast('Entry restored', 'success');
  loadArchive();
}

// ===== REFRESH =====
function refresh() {
  document.getElementById('current-date').textContent = formatDate(currentDate);
  loadEntries();
  loadSuggestions();
  loadDayMeta();
  loadConnectors();
}

// ===== INIT =====
refresh();
if (typeof lucide !== 'undefined') lucide.createIcons();
