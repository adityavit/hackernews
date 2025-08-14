const isSameOriginApi = !location.port || location.port === "5000";
const API_BASE = window.API_BASE_URL || (isSameOriginApi ? "" : `http://${location.hostname}:5000`);
const API_URL = `${API_BASE}/api/top-stories`;

function setStatus(message) {
  const status = document.getElementById("status");
  status.textContent = message || "";
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


