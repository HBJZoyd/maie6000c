'use strict';
const $ = (id) => document.getElementById(id);
let records = [], activeId = null, ready = false, sending = false, pollTimer = null;
let submission = null;
const states = {queued: '排队中', processing: '正在查阅手册', answered: '回答完成', failed: '处理失败'};
const pending = (record) => ['queued', 'processing'].includes(record.status);
const dateLabel = (value) => new Intl.DateTimeFormat('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(value));

async function request(path, options = {}) {
  const response = await fetch(path, {...options,
    headers:{'Content-Type':'application/json', ...(options.headers || {})}});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : '请求未完成，请稍后重试。');
  }
  return response.json();
}
function notice(message) { $('notice').textContent = message || ''; $('notice').hidden = !message; }
function updateSend() {
  $('send-button').disabled = sending || !ready || $('question-input').value.trim().length < 3;
  $('char-count').textContent = `${$('question-input').value.length} / 4000`;
}
function upsert(record) {
  records = [record, ...records.filter(item => item.id !== record.id)]
    .sort((a,b) => new Date(b.created_at) - new Date(a.created_at));
  renderHistory();
}
function renderHistory() {
  const history = $('history'); history.replaceChildren();
  $('history-count').textContent = records.length;
  if (!records.length) {
    const empty = document.createElement('p'); empty.className = 'empty-history';
    empty.textContent = '你的问题和答案会保存在这里。'; history.append(empty); return;
  }
  for (const record of records) {
    const button = document.createElement('button'); button.className = 'history-item';
    button.setAttribute('aria-pressed', String(activeId === record.id)); button.title = record.question;
    const title = document.createElement('span'); title.className = 'history-title'; title.textContent = record.question;
    const meta = document.createElement('span'); meta.className = 'history-meta';
    const time = document.createElement('span'); time.textContent = dateLabel(record.created_at);
    const status = document.createElement('span'); status.textContent = states[record.status] || record.status;
    meta.append(time,status); button.append(title,meta); button.addEventListener('click',() => selectRecord(record)); history.append(button);
  }
}
function renderRecord(record) {
  $('welcome').hidden = true; $('conversation').hidden = false;
  $('question-text').textContent = record.question; $('answer-state').textContent = states[record.status] || '';
  if (record.status === 'answered') {
    const labels = {needs_clarification:'需要补充信息', insufficient_evidence:'手册证据不足'};
    $('answer-state').textContent = labels[record.answer_type] || states.answered;
  }
  const content = $('answer-content'); content.replaceChildren(); content.className = 'answer-content';
  $('source-section').hidden = true; $('copy-answer').hidden = true; $('retry-question').hidden = true;
  $('answer-time').textContent = '';
  if (pending(record)) {
    content.classList.add('pending'); const dots = document.createElement('span'); dots.className = 'thinking';
    dots.setAttribute('aria-hidden','true'); for (let i=0;i<3;i++) dots.append(document.createElement('i'));
    content.append(dots, document.createTextNode(record.status === 'queued' ? '问题已保存，等待车书助手处理…' : '正在检索手册、核对相关内容并整理答案…'));
    return;
  }
  if (record.status === 'failed') {
    content.classList.add('failed'); content.textContent = record.error || '服务暂时无法回答，请稍后重试。';
    $('retry-question').hidden = false; return;
  }
  content.textContent = record.answer || '手册中未找到可用答案。'; $('copy-answer').hidden = !record.answer;
  $('answer-time').textContent = dateLabel(record.updated_at) + (record.manual ?
    ` · ${record.manual.manual_version}` : ' · 历史记录：手册版本未标注');
  if (record.provenance?.mode === 'fixture') {
    const warning = document.createElement('p'); warning.textContent =
      record.provenance.model_id === 'recorded-w07-no-model-call' ?
      '模拟演示 · 历史回答回放（录制日期：2026-10-31）' : '离线工程测试：模拟结果，未调用真实 AI。';
    content.prepend(warning);
  }
  const pages = $('page-links'), excerpts = $('source-excerpts'), images = $('related-images');
  document.querySelector('.source-heading span').textContent =
    record.provenance?.model_id === 'recorded-w07-no-model-call' ?
    '点击页码查看演示摘录；原手册页码见标题' : '点击页码查看原始手册';
  pages.replaceChildren(); excerpts.replaceChildren(); images.replaceChildren();
  for (const page of record.cite_pages || []) {
    const link = document.createElement('a'); link.className = 'page-link'; link.href = `/manual.pdf#page=${page}`;
    if (record.manual) link.href = `/manual.pdf?sha256=${record.manual.document_sha256}#page=${page}`;
    link.target = '_blank'; link.rel = 'noopener';
    link.textContent = record.provenance?.model_id === 'recorded-w07-no-model-call' ?
      `演示摘录第 ${page} 页 ↗` : `手册第 ${page} 页 ↗`; pages.append(link);
  }
  for (const source of record.sources || []) {
    const detail = document.createElement('details'); detail.className = 'source-detail';
    const summary = document.createElement('summary'); summary.textContent = `${source.title} · 第 ${source.page} 页`;
    const text = document.createElement('p'); text.textContent = source.excerpt;
    detail.append(summary,text); excerpts.append(detail);
  }
  for (const image of record.related_images || []) {
    const figure = document.createElement('figure'); const link = document.createElement('a');
    link.href = `/manual-images/${image.id}`; link.target = '_blank'; link.rel = 'noopener';
    const img = document.createElement('img'); img.src = link.href; img.alt = image.title; img.loading = 'lazy';
    const caption = document.createElement('figcaption'); caption.textContent = `${image.title} · 第 ${image.page} 页`;
    link.append(img); figure.append(link,caption); images.append(figure);
  }
  $('source-section').hidden = !(record.cite_pages?.length || record.related_images?.length);
}
function selectRecord(record) {
  activeId = record.id; clearTimeout(pollTimer); notice(''); renderHistory(); renderRecord(record);
  $('sidebar').classList.remove('open'); $('toggle-history').setAttribute('aria-expanded','false');
  if (pending(record)) pollTimer = setTimeout(() => poll(record.id), 1000);
}
async function poll(id) {
  if (id !== activeId) return;
  try {
    const record = await request(`/questions/${id}`); upsert(record);
    if (id !== activeId) return;
    renderRecord(record); notice('');
    if (pending(record)) pollTimer = setTimeout(() => poll(id), 1500);
  } catch {
    if (id !== activeId) return;
    notice('暂时无法获取回答进度，正在重新连接；已提交的问题会继续处理。');
    pollTimer = setTimeout(() => poll(id), 4000);
  }
}
async function loadHistory() {
  try { records = await request('/questions?limit=50'); renderHistory(); }
  catch { notice('历史提问暂时无法读取，请检查项目服务是否正常运行。'); }
}
async function checkConnection() {
  try { const status = await request('/system/status'); ready = status.rag === 'ready';
    window.backendMode = status.mode; window.demoKind = status.demo_kind; }
  catch { ready = false; }
  $('connection').className = `connection ${ready ? 'ready' : 'unavailable'}`;
  $('connection').querySelector('span').textContent = ready ?
    (window.backendMode === 'fixture' ? '离线工程测试（模拟）' : '车书服务已连接') : '车书服务未连接';
  $('composer-note').textContent = ready ? '回答依据已收录的手册，功能可能随车型年份、配置及软件版本不同。' : '问答服务尚未连接。历史记录仍可查看，连接后即可开始提问。';
  if (ready && window.backendMode === 'fixture') {
    $('composer-note').textContent = '当前为离线工程测试：仅验证提交、异步处理和保存，不调用真实 AI。';
  }
  if (ready && window.demoKind === 'recorded-replay') {
    $('connection').querySelector('span').textContent = '模拟演示 · 历史回放';
    $('composer-note').textContent = '演示使用已录制的哨兵模式回答，提交、后台处理与保存实时运行。';
    $('manual-link').textContent = '演示摘录 ↗';
    const suggestions = document.querySelectorAll('[data-question]');
    suggestions[0].querySelector('strong').textContent = '哨兵模式演示';
    suggestions[1].dataset.question = '这个功能怎么设置？';
    suggestions[1].querySelector('strong').textContent = '演示范围之外';
    suggestions[1].querySelector('small').textContent = '展示明确的范围提示';
    suggestions[2].dataset.question = 'Model 3 明年的保险价格是多少？';
    suggestions[2].querySelector('strong').textContent = '不支持的问题';
    suggestions[2].querySelector('small').textContent = '展示不编造回答的结果';
  }
  updateSend();
}
$('question-input').addEventListener('input', updateSend);
$('question-input').addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault(); if (!$('send-button').disabled) $('question-form').requestSubmit();
  }
});
$('question-form').addEventListener('submit', async event => {
  event.preventDefault(); if ($('send-button').disabled) return;
  sending = true; updateSend(); notice('');
  try {
    const question = $('question-input').value.trim();
    if (!submission || submission.question !== question) submission = {question, key:crypto.randomUUID()};
    const record = await request('/questions', {method:'POST',
      headers:{'Idempotency-Key':submission.key},body:JSON.stringify({question})});
    submission = null;
    $('question-input').value = ''; upsert(record); selectRecord(record);
  } catch (error) { notice(error.message); }
  finally { sending = false; updateSend(); }
});
$('new-question').addEventListener('click', () => {
  activeId = null; clearTimeout(pollTimer); $('welcome').hidden = false; $('conversation').hidden = true;
  notice(''); renderHistory(); $('sidebar').classList.remove('open');
  $('toggle-history').setAttribute('aria-expanded','false'); $('question-input').focus();
});
document.querySelectorAll('[data-question]').forEach(button => button.addEventListener('click', () => {
  $('question-input').value = button.dataset.question; updateSend(); $('question-input').focus();
}));
$('toggle-history').addEventListener('click', () => {
  const open = $('sidebar').classList.toggle('open'); $('toggle-history').setAttribute('aria-expanded',String(open));
});
$('copy-answer').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(records.find(record => record.id === activeId)?.answer || '');
    $('copy-answer').textContent = '已复制'; setTimeout(() => $('copy-answer').textContent = '复制答案',1500);
  } catch { notice('未能自动复制，请选中答案文字手动复制。'); }
});
$('retry-question').addEventListener('click', async () => {
  const id = activeId; $('retry-question').disabled = true;
  try { const record = await request(`/questions/${id}/retry`,{method:'POST'}); upsert(record);
    if (activeId === id) selectRecord(record);
  } catch (error) { notice(error.message); }
  finally { $('retry-question').disabled = false; }
});
loadHistory(); checkConnection(); setInterval(checkConnection,15000);
