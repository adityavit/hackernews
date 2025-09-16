const isSameOriginApi = !location.port || location.port === "5000";
const API_BASE = window.API_BASE_URL || (isSameOriginApi ? "" : `http://${location.hostname}:8081`);
const API_URL = `${API_BASE}/api/top-stories`;
const SUMMARY_URL = (id, params = "") => `${API_BASE}/api/stories/${id}/comments/summary${params ? `?${params}` : ""}`;

function setStatus(message) {
  const status = document.getElementById("status");
  status.textContent = message || "";
}

function updateFetchedAt(timestamp) {
  const el = document.getElementById("fetchedAt");
  if (!el) return;

  if (!timestamp) {
    el.textContent = "";
    el.hidden = true;
    el.removeAttribute('title');
    return;
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    el.textContent = `Fetched at ${timestamp}`;
    el.hidden = false;
    el.removeAttribute('title');
    return;
  }

  const formatted = formatFetchTimestamp(date);
  el.textContent = `Fetched ${formatted}`;
  el.hidden = false;
  el.title = date.toISOString();
}

function formatFetchTimestamp(date) {
  const formatter = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const label = formatter.format(date);
  return timezone ? `${label} (${timezone})` : label;
}

function renderSummary(container, data) {
  const content = container.querySelector('.summary-content');
  const { summary, top_comments } = data || {};
  const exec = (summary && summary.executive_summary) || "No summary available.";
  const bullets = (summary && Array.isArray(summary.key_points)) ? summary.key_points : [];
  const steps = (summary && Array.isArray(summary.next_steps)) ? summary.next_steps : [];

  const parts = [];
  parts.push(`<h3>Executive summary</h3><p>${escapeHtml(exec)}</p>`);
  if (bullets.length) {
    parts.push('<h3>Key points</h3><ul>');
    for (const b of bullets) parts.push(`<li>${escapeHtml(b)}</li>`);
    parts.push('</ul>');
  }
  if (steps.length) {
    parts.push('<h3>Next steps</h3><ul>');
    for (const s of steps) parts.push(`<li>${escapeHtml(s)}</li>`);
    parts.push('</ul>');
  }
  if (Array.isArray(top_comments) && top_comments.length) {
    parts.push('<h3>Top comments</h3><ul>');
    for (const c of top_comments.slice(0, 5)) {
      const label = `${c.author || ''} (${c.stance || ''}) – ${Number(c.must_read_score||0).toFixed(2)}`.trim();
      parts.push(`<li>${escapeHtml(label)}: ${escapeHtml((c.text||'').slice(0,160))}</li>`);
    }
    parts.push('</ul>');
  }
  content.innerHTML = parts.join('');
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function createStoryElement(story) {
  const template = document.getElementById("story-item-template");
  const node = template.content.cloneNode(true);

  // annotate root <li> with story id for delegated handlers
  const root = node.querySelector('li.story');
  if (root) root.dataset.storyId = String(story.id || '');

  const link = node.querySelector(".story-link");
  link.textContent = story.title || "Untitled";
  link.href = story.url || "#";

  const score = node.querySelector(".score");
  score.textContent = typeof story.score === "number" ? story.score : 0;

  const user = node.querySelector(".user");
  user.textContent = story.user ? `by ${story.user}` : "";

  const age = node.querySelector(".age");
  age.textContent = story.age || "";

  const comments = node.querySelector(".comments");
  comments.textContent = typeof story.comments === "number" ? story.comments : 0;

  return node;
}

async function handleSummaryToggle({ button, panel, storyId }) {
  console.log("handleSummaryToggle", { button, panel, storyId });
  const expanded = button.getAttribute('aria-expanded') === 'true';
  if (expanded) {
    panel.hidden = true;
    button.setAttribute('aria-expanded', 'false');
    button.textContent = 'View summary';
    return;
  }
  button.disabled = true;
  button.textContent = 'Loading…';
  try {
    const url = SUMMARY_URL(storyId, 'max_depth=1&limit=40');
    const res = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderSummary(panel, data);
    panel.hidden = false;
    button.setAttribute('aria-expanded', 'true');
    button.textContent = 'Hide summary';
  } catch (e) {
    panel.hidden = false;
    panel.querySelector('.summary-content').innerHTML = `<p>Failed to load summary: ${escapeHtml(e.message)}</p>`;
    button.setAttribute('aria-expanded', 'true');
    button.textContent = 'Hide summary';
  } finally {
    button.disabled = false;
  }
}

async function loadStories() {
  console.log("loadStories");
  const list = document.getElementById("stories");
  list.innerHTML = "";
  setStatus("Loading...");
  updateFetchedAt(null);

  try {
    const response = await fetch(API_URL, { headers: { Accept: "application/json" } });
    console.log("loadStories response", response);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();

    let stories;
    let generatedAt;
    if (Array.isArray(payload)) {
      stories = payload;
    } else if (payload && typeof payload === 'object') {
      if (!Array.isArray(payload.data)) {
        throw new Error("Invalid payload: missing data array");
      }
      stories = payload.data;
      generatedAt = payload.generated_at || payload.generatedAt || null;
    } else {
      throw new Error("Invalid payload format");
    }

    updateFetchedAt(generatedAt);

    if (stories.length === 0) {
      setStatus("No stories found.");
      return;
    }

    const fragment = document.createDocumentFragment();
    for (const story of stories) {
      fragment.appendChild(createStoryElement(story));
    }
    list.appendChild(fragment);
    setStatus("");
  } catch (err) {
    setStatus(`Failed to load stories: ${err.message}`);
    updateFetchedAt(null);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn.addEventListener("click", loadStories);
  // delegated click handler for summary toggle
  const list = document.getElementById('stories');
  list.addEventListener('click', (e) => {
    const btn = e.target.closest('.summary-link');
    if (!btn) return;
    const item = btn.closest('li.story');
    if (!item) return;
    const panel = item.querySelector('.summary-panel');
    const storyId = item.dataset.storyId;
    handleSummaryToggle({ button: btn, panel, storyId });
  });
  loadStories();
});
