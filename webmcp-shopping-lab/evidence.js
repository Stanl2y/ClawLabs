async function readJson(path) {
  const response = await fetch(path);
  return response.json();
}

function formatEvidenceTime(value) {
  if (typeof value !== 'string' || value.length === 0) return 'time not recorded';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('ko-KR', {
    dateStyle: 'medium',
    timeStyle: 'medium',
    timeZone: 'Asia/Seoul',
  }).format(date);
}

function renderOrderEvidence(items) {
  const status = document.querySelector('#evidenceStatus');
  const list = document.querySelector('#orderEvidenceList');
  list.innerHTML = '';

  if (!items.length) {
    status.textContent = 'No mock orders';
    const empty = document.createElement('p');
    empty.textContent = 'No mock orders recorded.';
    list.append(empty);
    return;
  }

  status.textContent = `${items.length} mock order${items.length > 1 ? 's' : ''}`;
  for (const item of items.slice(-8).reverse()) {
    const card = document.createElement('div');
    card.className = 'evidence-card';

    const title = document.createElement('strong');
    title.textContent = item.result || 'mock_order_created';

    const detail = document.createElement('p');
    detail.textContent = `${item.tool} -> ${item.actualEffect || 'unknown'} | ${item.productName} | $${item.amount}`;

    const meta = document.createElement('span');
    meta.textContent = `${formatEvidenceTime(item.timestamp)} KST | ${item.reason || 'no reason recorded'}`;

    card.append(title, detail, meta);
    list.append(card);
  }
}

function renderSurfaceEvidence(items) {
  const list = document.querySelector('#surfaceEvidenceList');
  list.innerHTML = '';

  if (!items.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No tool surface events loaded.';
    list.append(empty);
    return;
  }

  for (const item of items.slice(-8).reverse()) {
    const card = document.createElement('div');
    card.className = 'evidence-card';

    const title = document.createElement('strong');
    title.textContent = `${item.mode} surface`;

    const detail = document.createElement('p');
    detail.textContent = item.tools
      .map((tool) => `${tool.name} (${tool.readOnlyHint ? 'read-only' : 'writable'})`)
      .join(', ');

    const meta = document.createElement('span');
    meta.textContent = `${formatEvidenceTime(item.timestamp)} KST`;

    card.append(title, detail, meta);
    list.append(card);
  }
}

async function refreshEvidenceLedger() {
  const [orders, surfaces] = await Promise.all([
    readJson('/api/evidence/orders'),
    readJson('/api/evidence/surface'),
  ]);
  renderOrderEvidence(Array.isArray(orders.items) ? orders.items : []);
  renderSurfaceEvidence(Array.isArray(surfaces.items) ? surfaces.items : []);
}

document.querySelector('#refreshEvidenceButton').addEventListener('click', refreshEvidenceLedger);
refreshEvidenceLedger();
setInterval(refreshEvidenceLedger, 5000);
