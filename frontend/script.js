

const API_URL = "https://areacane.onrender.com/api/alerts";

const form = document.getElementById("zip-form");
const zipInput = document.getElementById("zip");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resultsEl.replaceChildren();
  statusEl.textContent = "Checking...";

  try {
    const res = await fetch(`${API_URL}?zip_code=${encodeURIComponent(zipInput.value.trim())}`);
    const data = await res.json();

    if (!res.ok) {
      statusEl.textContent = data.error || "Something went wrong.";
      return;
    }

    statusEl.textContent =
      `${data.location.city}, ${data.location.state}: ` +
      (data.number_of_alerts === 0
        ? "no active hurricane or tropical storm alerts."
        : `${data.number_of_alerts} active alert(s).`);

    for (const alert of data.alerts) {
      const card = document.createElement("article");
      card.className = "alert-card";

      const title = document.createElement("h2");
      title.textContent = alert.event;

      const headline = document.createElement("p");
      headline.textContent = alert.headline;

      const area = document.createElement("p");
      area.className = "alert-area";
      area.textContent = alert.area;

      card.append(title, headline, area);
      resultsEl.append(card);
    }
  } catch (err) {
    statusEl.textContent = "Can't reach the server. Is the backend running?";
  }
});