# =============================================================================
# Areacane backend
#
# A small Flask API that looks up official National Weather Service (NWS)
# alerts for a US ZIP code. The frontend sends a ZIP code, and this server
# returns any active hurricane/tropical alerts for that location.
#
# Routes:
#   GET  /api/health  -> confirms the server is running
#   POST /api/verify  -> placeholder: accepts alert text (not yet verified)
#   GET  /api/alerts  -> main route: ZIP code in, official NWS alerts out
#
# Environment variables:
#   ALLOWED_ORIGINS  Comma-separated list of frontend addresses allowed to call
#                    this API from a browser (no spaces, no trailing slashes).
#                    Defaults to http://localhost:3000 for local development.
#   FLASK_DEBUG      Set to "1" for debug mode (local use only, never in
#                    production).
#
# Modules used:
#   Flask    - creates the web application/server
#   request  - reads data sent by the frontend (query parameters, JSON body)
#   jsonify  - converts Python dictionaries into JSON responses
#   CORS     - lets a browser-based frontend on another address call this API
#   requests - makes outgoing HTTP calls to the ZIP code and NWS services
# =============================================================================

import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Create the Flask application object. Gunicorn runs it in production
# with the command: gunicorn app:app
app = Flask(__name__)

# Browsers block a page on one address from reading responses from another
# address unless the server explicitly allows it (CORS). Read the allowed
# frontend addresses from the ALLOWED_ORIGINS environment variable, falling
# back to the local development frontend. split(",") turns the comma-separated
# string into a list, so several origins can be allowed at once.
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins = allowed_origins)

# Maximum number of characters accepted by /api/verify, to reject huge inputs.
MAX_ALERT_LENGTH = 5000


# -----------------------------------------------------------------------------
# GET /api/health
# Simple check that the server is up. Useful for testing a deployment.
# -----------------------------------------------------------------------------
@app.route("/api/health", methods = ["GET"]) 
def health():
    return jsonify({"message": "Areacane backend is running"})


# -----------------------------------------------------------------------------
# POST /api/verify
# Placeholder route. Expects JSON like {"alert_text": "..."}. It validates the
# input and echoes it back with the status "unverified". No real verification
# happens yet, and the current frontend (ZIP code only) does not use it.
# -----------------------------------------------------------------------------
@app.route("/api/verify", methods= ["POST"])
def verify():
    # Parse the JSON body. silent=True returns None instead of raising an
    # error when the body is missing or malformed, so "or {}" gives an empty
    # dictionary in that case.
    data = request.get_json(silent = True) or {}
    alert = data.get("alert_text")

    # Reject anything that isn't a non-empty string (missing, null, a number,
    # or only whitespace).
    if not isinstance(alert,str) or not alert.strip():
        return jsonify({"error": "Please submit an alert as non-empty text."}), 400

    # Remove leading/trailing whitespace before measuring and returning it.
    alert = alert.strip()

    # 413 means the submitted content is too large.
    if len(alert) > MAX_ALERT_LENGTH:
        return jsonify ({
            "error": f"Alert is too long (max {MAX_ALERT_LENGTH} characters)."

        }), 413

    # Nothing is actually checked yet, so the status is always "unverified".
    return jsonify ({
        "status": "unverified",
        "message": "Alert received successfully.",
        "submitted_alert": alert,

    })


# NWS event names (lowercase) that count as hurricane/tropical alerts. Only
# alerts whose event name appears in this set are returned by /api/alerts.
# Names are lowercase because the code compares event.lower() against them.
TROPICAL_EVENTS = {

    "hurricane warning", "hurricane watch", "hurricane local statement", 
    "tropical storm warning", "tropical storm watch", 
    "storm surge warning", "storm surge watch", "extreme wind warning",
    # NOTE: not a tropical alert. This entry was added temporarily to test the
    # pipeline with a real active alert. Remove it to return tropical alerts only.
    "coastal flood statement",

}


# -----------------------------------------------------------------------------
# GET /api/alerts?zip_code=12345
# Main route. Steps:
#   1. Validate the ZIP code from the URL.
#   2. Convert the ZIP code to latitude/longitude (Zippopotam API).
#   3. Ask the NWS for active alerts at that point.
#   4. Keep only the tropical alerts and return them as JSON.
# -----------------------------------------------------------------------------
@app.route("/api/alerts", methods = ["GET"])
def get_alerts():
    # Read zip_code from the query string. The default is a single space,
    # which strip() turns into an empty string, so a missing ZIP fails the
    # validation check below.
    zip_code = request.args.get("zip_code", " ").strip()

    # Must be exactly 5 ASCII digits. isascii() blocks look-alike Unicode
    # digits that isdigit() alone would accept.
    if not (zip_code.isascii() and zip_code.isdigit() and len(zip_code) == 5): 
        return jsonify({"error": "Enter a valid 5 digit ZIP code."}), 400  

    # Both outside services can fail (network problems, timeouts, unexpected
    # responses), so everything that talks to them is wrapped in try/except.
    try: 

        # --- Step 1: ZIP code -> coordinates (Zippopotam, a free third-party
        # service). The timeout stops the request hanging forever.
        zip_response = requests.get(f"https://api.zippopotam.us/us/{zip_code}", timeout = 10 )

        # A 404 means the ZIP code doesn't exist.
        if zip_response.status_code == 404:
            return jsonify({"error": "ZIP code not found."}), 404

        # Raise an exception for any other HTTP error (caught below).
        zip_response.raise_for_status()

        # Take the first place listed for the ZIP code. The API returns the
        # coordinates as strings, so convert them to numbers and round to
        # 4 decimal places, which the NWS point lookup accepts.
        place = zip_response.json()["places"][0]
        latitude = round(float(place["latitude"]), 4)
        longitude = round(float(place["longitude"]), 4)

        # --- Step 2: ask the NWS for alerts currently active at that point.
        # The NWS requires a User-Agent that identifies the app and gives a
        # contact address. Accept asks for GeoJSON, the NWS alert format.
        nws_response = requests.get(
            "https://api.weather.gov/alerts/active",
            params = {"point": f"{latitude},{longitude}"}, 
            headers = {
                "User-Agent": "Areacane/1.0 (sharkbyteproject2026@gmail.com)",
                "Accept": "application/geo+json", 
            }, 
            timeout = 10,
        )

        # Raise an exception if the NWS returned an HTTP error.
        nws_response.raise_for_status()

        # --- Step 3: filter. Each "feature" in the response is one alert.
        # .get() with defaults avoids crashing if a field is missing.
        alerts = []
        for feature in nws_response.json().get("features", []):
            details = feature.get("properties", {})
            event = details.get("event", " ")

            # Keep the alert only if its event type is in TROPICAL_EVENTS.
            if event.lower() in TROPICAL_EVENTS:
                alerts.append({
                    "event": event,                              # e.g. "Hurricane Warning"
                    "headline": details.get("headline"),         # one-line summary
                    "area": details.get("areaDesc"),             # affected areas
                    "severity": details.get("severity"),         # e.g. "Minor", "Severe"
                    "expires": details.get("expires"),           # when the alert expires
                    "instruction": details.get("instruction"),   # recommended action
                    "description": details.get("description"),   # full alert text
                    "source": "National Weather Service",
                    "api_url": feature.get("id"),                # link to the official record
                })

        # --- Step 4: return the location and alerts. An empty "alerts" list
        # means no tropical alerts, not that no hazards of any kind are active.
        return jsonify({

            "zip_code": zip_code,
            "location": {
                "city": place["place name"],
                "state": place["state"],
                "latitude": latitude,
                "longitude": longitude,
             },
            "number_of_alerts": len(alerts),
            "alerts": alerts,
        })        

    # A network failure, timeout, or HTTP error from either service. Log the
    # real error for debugging and send the user a generic message.
    # 502 means a service this server depends on failed.
    except requests.RequestException as e:
        app.logger.error("Request failed: %s", e)
        return jsonify({"error": "Unable to retrieve weather alerts. Try Again."}), 502
    
    # The ZIP service returned data in an unexpected shape (missing field,
    # empty list, or a value that can't be converted to a number).
    except (KeyError, IndexError, ValueError):
        return jsonify({"error": "Unable to process location information."}), 502



# Runs only when started with "python app.py" (local development), not under
# gunicorn. Debug mode (auto-reload and detailed errors) turns on only when
# FLASK_DEBUG=1 is set. Port 5001 is used because macOS reserves port 5000.
if __name__ == "__main__":
    app.run(debug = os.environ.get("FLASK_DEBUG") == "1", port = 5001)