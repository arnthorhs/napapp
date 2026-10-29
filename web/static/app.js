const childInput = document.getElementById("child");
const statusText = document.getElementById("status");
const toggleButton = document.getElementById("toggle");
const averageText = document.getElementById("average");
const dailyText = document.getElementById("daily");
const napList = document.getElementById("naps");
const errorText = document.getElementById("error");

let ongoingNap = null;

async function api(method, path, body) {
  const response = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(typeof data.detail === "string" ? data.detail : `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function time(iso) {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function day(iso) {
  return new Date(iso).toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}

function minutes(nap) {
  return Math.round((new Date(nap.end) - new Date(nap.start)) / 60000);
}

function napItem(nap) {
  const item = document.createElement("li");
  const text = document.createElement("span");
  text.textContent = nap.end
    ? `${day(nap.start)} ${time(nap.start)} – ${time(nap.end)}, ${minutes(nap)} min`
    : `${day(nap.start)} ${time(nap.start)} – …, ongoing`;
  const deleteButton = document.createElement("button");
  deleteButton.textContent = "×";
  deleteButton.onclick = () => removeNap(nap);
  item.append(text, deleteButton);
  return item;
}

async function refresh() {
  const child = childInput.value.trim();
  errorText.textContent = "";
  statusText.textContent = "";
  averageText.textContent = "";
  dailyText.textContent = "";
  napList.replaceChildren();
  toggleButton.hidden = true;
  if (!child) return;
  try {
    const since = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
    const naps = await api("GET", `/api/naps?${new URLSearchParams({ child_id: child, since })}`);
    ongoingNap = naps.find((nap) => nap.end === null) || null;
    statusText.textContent = ongoingNap ? `Napping since ${time(ongoingNap.start)}` : "Awake";
    toggleButton.textContent = ongoingNap ? "End nap" : "Start nap";
    toggleButton.hidden = false;
    napList.replaceChildren(...naps.map(napItem));
    const stats = await api("GET", `/api/stats/${encodeURIComponent(child)}`);
    averageText.textContent = stats.average_minutes === null
      ? "No finished naps in the last 7 days"
      : `Average nap, last 7 days: ${stats.average_minutes} min`;
    if (stats.nap_count > 0) {
      dailyText.textContent = `Nap sleep per day, last 7 days: ${stats.daily_minutes} min`;
    }
  } catch (error) {
    errorText.textContent = error.message;
  }
}

async function toggleNap() {
  toggleButton.disabled = true;
  try {
    const now = new Date().toISOString();
    if (ongoingNap) {
      await api("POST", `/api/naps/${ongoingNap.id}`, { end: now });
    } else {
      await api("POST", "/api/naps", { child_id: childInput.value.trim(), start: now });
    }
    await refresh();
  } catch (error) {
    errorText.textContent = error.message;
  } finally {
    toggleButton.disabled = false;
  }
}

async function removeNap(nap) {
  if (!confirm("Delete this nap?")) return;
  try {
    await api("DELETE", `/api/naps/${nap.id}`);
    await refresh();
  } catch (error) {
    errorText.textContent = error.message;
  }
}

childInput.value = localStorage.getItem("child") || "";
childInput.onchange = () => {
  localStorage.setItem("child", childInput.value.trim());
  refresh();
};
toggleButton.onclick = toggleNap;
refresh();
