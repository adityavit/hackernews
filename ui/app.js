const isSameOriginApi = !location.port || location.port === "5000";
const API_BASE = window.API_BASE_URL || (isSameOriginApi ? "" : `http://${location.hostname}:5000`);
const API_URL = `${API_BASE}/api/top-stories`;
const SUMMARY_URL = (id, params = "") => `${API_BASE}/api/stories/${id}/comments/summary${params ? `?${params}` : ""}`;

function setStatus(message) {
  const status = document.getElementById("status");
  status.textContent = message || "";
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

  const summaryBtn = node.querySelector('.summary-link');
  const panel = node.querySelector('.summary-panel');
  summaryBtn.addEventListener('click', async () => {
    const expanded = summaryBtn.getAttribute('aria-expanded') === 'true';
    if (expanded) {
      panel.hidden = true;
      summaryBtn.setAttribute('aria-expanded', 'false');
      summaryBtn.textContent = 'View summary';
      return;
    }
    summaryBtn.disabled = true;
    summaryBtn.textContent = 'Loading…';
    try {
      const url = SUMMARY_URL(story.id, 'max_depth=1&limit=40');
      const res = await fetch(url, { headers: { Accept: 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      renderSummary(panel, data);
      panel.hidden = false;
      summaryBtn.setAttribute('aria-expanded', 'true');
      summaryBtn.textContent = 'Hide summary';
    } catch (e) {
      panel.hidden = false;
      panel.querySelector('.summary-content').innerHTML = `<p>Failed to load summary: ${escapeHtml(e.message)}</p>`;
      summaryBtn.setAttribute('aria-expanded', 'true');
      summaryBtn.textContent = 'Hide summary';
    } finally {
      summaryBtn.disabled = false;
    }
  });

  return node;
}

async function loadStories() {
  const list = document.getElementById("stories");
  list.innerHTML = "";
  setStatus("Loading...");

  try {
    const response = await fetch(API_URL, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const stories = await response.json();
    if (!Array.isArray(stories)) {
      throw new Error("Invalid payload");
    }

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
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn.addEventListener("click", loadStories);
  loadStories();
});


