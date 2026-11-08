// =============================================================================
// Areacane frontend script
//
// Runs in the browser on index.html. When the user submits a ZIP code, it asks
// the Areacane backend for active hurricane/tropical alerts and shows the
// result on the page.
//
// Elements it expects in index.html (matched by id):
//   #zip-form  the form containing the ZIP input and the button
//   #zip       the ZIP code text input
//   #status    a paragraph for status and error messages
//   #results   a container where alert cards are added
// =============================================================================

// Address of the deployed backend route that returns alerts for a ZIP code.
// For local testing, temporarily change it to "http://localhost:5001/api/alerts".
const API_URL = "https://areacane.onrender.com/api/alerts";

// Grab the page elements once, so the code below can reuse them.
const form = document.getElementById("zip-form");
const zipInput = document.getElementById("zip");
const statusEl = document.getElementById("status");
const resultsEl = document.getElementById("results");

// Runs every time the form is submitted (button click or pressing Enter).
// "async" lets the function wait for the network request with "await".
form.addEventListener("submit", async (event) => {
  // Stop the browser's default behavior of reloading the page on submit.
  event.preventDefault();

  // Clear any alert cards from a previous search and show a loading message.
  // The first request can be slow if the free backend was asleep.
  resultsEl.replaceChildren();
  statusEl.textContent = "Checking...";

  // Network requests can fail, so everything below is wrapped in try/catch.
  try {
    // Ask the backend for alerts. trim() removes stray spaces, and
    // encodeURIComponent makes the ZIP safe to place in a URL.
    const res = await fetch(`${API_URL}?zip_code=${encodeURIComponent(zipInput.value.trim())}`);

    // Parse the JSON body. This is done before checking res.ok because the
    // backend sends error messages as JSON too.
    const data = await res.json();

    // res.ok is false for HTTP errors (400 invalid ZIP, 404 not found,
    // 502 service failure). Show the backend's message and stop.
    if (!res.ok) {
      statusEl.textContent = data.error || "Something went wrong.";
      return;
    }

    // Show the city and state, then either a "no alerts" message or the
    // number of active alerts. Zero alerts means no tropical alerts, not that
    // no hazards of any kind are active.
    statusEl.textContent =
      `${data.location.city}, ${data.location.state}: ` +
      (data.number_of_alerts === 0
        ? "no active hurricane or tropical storm alerts."
        : `${data.number_of_alerts} active alert(s).`);

    // Build one card on the page for each alert returned by the backend.
    for (const alert of data.alerts) {
      const card = document.createElement("article");
      card.className = "alert-card";

      // The alert type, such as "Hurricane Warning".
      const title = document.createElement("h2");
      title.textContent = alert.event;

      // The NWS one-line summary of the alert.
      const headline = document.createElement("p");
      headline.textContent = alert.headline;

      // The areas affected by the alert.
      const area = document.createElement("p");
      area.className = "alert-area";
      area.textContent = alert.area;

      // textContent is used above instead of innerHTML so text from the API
      // is always shown as plain text and can never run as HTML or code.

      // Put the pieces into the card, then add the card to the page.
      card.append(title, headline, area);
      resultsEl.append(card);
    }
  } catch (err) {
    // Reached when the request itself fails: the server is unreachable, the
    // connection drops, or the browser blocks the response (for example a
    // CORS error because ALLOWED_ORIGINS on the backend doesn't match this
    // page's address).
    statusEl.textContent = "Can't reach the server. Is the backend running?";
  }
});