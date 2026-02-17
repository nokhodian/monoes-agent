const API = '/api';

const actionsBody = document.getElementById('actions-body');
const actionsSkeleton = document.getElementById('actions-skeleton');
const refreshBtn = document.getElementById('refresh');
const qInput = document.getElementById('q');
const stateSelect = document.getElementById('state');

const targetsBody = document.getElementById('targets-body');
const targetsSkeleton = document.getElementById('targets-skeleton');
const actionIdInput = document.getElementById('actionId');
const loadTargetsBtn = document.getElementById('loadTargets');

const overlay = document.getElementById('detail-overlay');
const detailPanel = document.querySelector('.detail-panel');
const detailClose = document.getElementById('detail-close');
const detailTitle = document.getElementById('detail-title');
const detailMeta = document.getElementById('detail-meta');
const detailTargetsSkeleton = document.getElementById('detail-targets-skeleton');
const detailTargets = document.getElementById('detail-targets');
const detailCollectedSkeleton = document.getElementById('detail-collected-skeleton');
const detailCollected = document.getElementById('detail-collected');
const createOverlay = document.getElementById('create-overlay');
const createClose = document.getElementById('create-close');
const newActionBtn = document.getElementById('newAction');
const toast = document.getElementById('toast');

function showSkeleton(container, rows = 6) {
  container.innerHTML = '';
  container.classList.remove('hidden');
  for (let i = 0; i < rows; i++) {
    const row = document.createElement('div');
    row.className = 'skeleton';
    container.appendChild(row);
  }
}
function hideSkeleton(container) {
  container.classList.add('hidden');
}

async function fetchActions() {
  showSkeleton(actionsSkeleton);
  const params = new URLSearchParams();
  const q = qInput.value.trim();
  const state = stateSelect.value.trim();
  if (q) params.set('q', q);
  if (state) params.set('state', state);
  const res = await fetch(`${API}/actions?${params.toString()}`);
  const data = await res.json();
  const items = (data.data && data.data.actions) || [];
  actionsBody.innerHTML = items.map(a => {
    const platformBadge = `<span class="badge platform">${a.targetPlatform || '-'}</span>`;
    const stateBadge = `<span class="badge state-${a.state}">${a.state}</span>`;
    return `<tr class="action-row" data-action-id="${a.id}">
      <td>${a.title || '-'}</td>
      <td>${a.type || '-'}</td>
      <td>${platformBadge}</td>
      <td>${stateBadge}</td>
      <td>${a.createdBy || '-'}</td>
    </tr>`;
  }).join('');
  bindActionRowClicks();
  hideSkeleton(actionsSkeleton);
}

async function fetchTargets(actionId) {
  showSkeleton(targetsSkeleton);
  const res = await fetch(`${API}/actions/${encodeURIComponent(actionId)}/targets`);
  const data = await res.json();
  const items = (data.data && data.data.actionTargets) || [];
  targetsBody.innerHTML = items.map(t => {
    const link = t.link ? `<a href="${t.link}" target="_blank" rel="noopener noreferrer">${t.link}</a>` : '-';
    return `<tr>
      <td>${t.personId || '-'}</td>
      <td>${t.platform || '-'}</td>
      <td>${link}</td>
      <td>${t.status || '-'}</td>
    </tr>`;
  }).join('');
  hideSkeleton(targetsSkeleton);
}

function openDetail() {
  overlay.classList.remove('hidden');
  requestAnimationFrame(() => {
    detailPanel.classList.add('in');
  });
}
function closeDetail() {
  detailPanel.classList.remove('in');
  setTimeout(() => overlay.classList.add('hidden'), 200);
}
detailClose.addEventListener('click', closeDetail);

async function populateDetail(actionId) {
  detailTargets.innerHTML = '';
  detailCollected.innerHTML = '';
  showSkeleton(detailTargetsSkeleton, 4);
  showSkeleton(detailCollectedSkeleton, 4);
  const [actionRes, targetsRes, collectedRes] = await Promise.all([
    fetch(`${API}/actions/${encodeURIComponent(actionId)}`),
    fetch(`${API}/actions/${encodeURIComponent(actionId)}/targets`),
    fetch(`${API}/actions/${encodeURIComponent(actionId)}/collected`)
  ]);
  const actionData = await actionRes.json();
  const targetsData = await targetsRes.json();
  const collectedData = await collectedRes.json();
  const a = actionData.data && actionData.data.action;
  if (a) {
    detailTitle.textContent = a.title || '';
    detailMeta.textContent = [a.type, a.state, a.targetPlatform].filter(Boolean).join(' • ');
  }
  const targets = (targetsData.data && targetsData.data.actionTargets) || [];
  detailTargets.innerHTML = targets.map(t => {
    const link = t.link ? `<a href="${t.link}" target="_blank" rel="noopener noreferrer">${t.link}</a>` : '-';
    return `<div class="target-card reveal">
      <div class="profile-meta">${t.platform} • ${t.status}</div>
      <div>${link}</div>
      <div>${t.personId}</div>
    </div>`;
  }).join('');
  hideSkeleton(detailTargetsSkeleton);
  const collected = (collectedData.data && collectedData.data.collected) || [];
  detailCollected.innerHTML = collected.map(p => {
    const link = p.link ? `<a href="${p.link}" target="_blank" rel="noopener noreferrer">${p.link}</a>` : '';
    return `<div class="profile-card reveal">
      <div class="profile-head">
        <div class="avatar" style="background-image:url('${p.image_url || ''}'); background-size:cover;"></div>
        <div>
          <div>${p.full_name || p.platform_username || '-'}</div>
          <div class="profile-meta">${p.category || ''} • ${p.follower_count || ''}</div>
        </div>
      </div>
      <div class="profile-meta">${p.introduction || ''}</div>
      <div>${link}</div>
    </div>`;
  }).join('');
  hideSkeleton(detailCollectedSkeleton);
  runReveal();
}

function bindActionRowClicks() {
  document.querySelectorAll('.action-row').forEach(row => {
    row.addEventListener('click', () => {
      const id = row.getAttribute('data-action-id');
      openDetail();
      populateDetail(id);
    });
  });
}

function runReveal() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
}

refreshBtn.addEventListener('click', fetchActions);
loadTargetsBtn.addEventListener('click', () => {
  const id = actionIdInput.value.trim();
  if (id) fetchTargets(id);
});

window.addEventListener('DOMContentLoaded', () => {
  setTimeout(fetchActions, 150);
  runReveal();
});

function openCreate() {
  createOverlay.classList.remove('hidden');
  requestAnimationFrame(() => {
    const panel = createOverlay.querySelector('.detail-panel');
    panel.classList.add('in');
  });
}
function closeCreate() {
  const panel = createOverlay.querySelector('.detail-panel');
  panel.classList.remove('in');
  setTimeout(() => createOverlay.classList.add('hidden'), 200);
}
newActionBtn.addEventListener('click', openCreate);
createClose.addEventListener('click', closeCreate);
document.getElementById('ca-cancel').addEventListener('click', closeCreate);
document.getElementById('create-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('ca-title').value.trim();
  const type = document.getElementById('ca-type').value;
  const state = document.getElementById('ca-state').value;
  const targetPlatform = document.getElementById('ca-platform').value;
  const createdBy = document.getElementById('ca-createdBy').value.trim();
  const ownerId = document.getElementById('ca-ownerId').value.trim();
  const contentSubject = document.getElementById('ca-subject').value.trim();
  const contentMessage = document.getElementById('ca-message').value.trim();
  const mediaRaw = document.getElementById('ca-media').value.trim();
  const scheduledDate = document.getElementById('ca-scheduled').value;
  const executionInterval = parseInt(document.getElementById('ca-interval').value || '0', 10);
  const startDate = document.getElementById('ca-start').value;
  const endDate = document.getElementById('ca-end').value;
  const campaignID = document.getElementById('ca-campaign').value.trim() || null;
  if (!title || !createdBy || !ownerId) {
    showToast('Please fill required fields.');
    return;
  }
  const contentBlobURL = mediaRaw ? mediaRaw.split(',').map(s => s.trim()).filter(Boolean) : [];
  const payload = {
    createdBy,
    ownerId,
    title,
    type,
    state,
    targetPlatform,
    contentSubject: contentSubject || null,
    contentMessage: contentMessage || null,
    contentBlobURL,
    scheduledDate: scheduledDate || null,
    executionInterval,
    startDate: startDate || null,
    endDate: endDate || null,
    campaignID
  };
  const res = await fetch(`${API}/actions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    showToast('Action created successfully.');
    closeCreate();
    fetchActions();
  } else {
    const text = await res.text();
    showToast('Failed to create action: ' + text);
  }
});

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove('hidden');
  requestAnimationFrame(() => toast.classList.add('in'));
  setTimeout(() => {
    toast.classList.remove('in');
    setTimeout(() => toast.classList.add('hidden'), 200);
  }, 3200);
}
