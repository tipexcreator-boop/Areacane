#
#
# Flask: creates backend web apllication/server
# request: receives information from frontend (a submitted hurricane alert)
# jonsify: Converts python data to JSON response for frontend
# CORS: Allows frontend and backend to communicate
import os
import requests
from flask import  Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins = allowed_origins)

MAX_ALERT_LENGTH = 5000 

# displays message when server runs successfully.
@app.route("/api/health", methods = ["GET"]) 
def health():
    return jsonify({"message": "Areacane backend is running"})


# verifies the hurricane alerts
@app.route("/api/verify", methods= ["POST"])
def verify():
    data = request.get_json(silent = True) or {}
    alert = data.get("alert_text")

    if not isinstance(alert,str) or not alert.strip():
        return jsonify({"error": "Please submit an alert as non-empty text."}), 400

    alert = alert.strip()

    if len(alert) > MAX_ALERT_LENGTH:
        return jsonify ({
            "error": f"Alert is too long (max {MAX_ALERT_LENGTH} characters)."

        }), 413

    return jsonify ({
        "status": "unverified",
        "message": "Alert received successfully.",
        "submitted_alert": alert,

    })


TROPICAL_EVENTS = {

    "hurricane warning", "hurricane watch", "hurricane local statement", 
    "tropical storm warning", "tropical storm watch", 
    "storm surge warning", "storm surge watch", "extreme wind warning",

}

# processes the zip-code
@app.route("/api/alerts", methods = ["GET"])
def get_alerts():
    zip_code = request.args.get("zip_code", " ").strip()

    if not (zip_code.isascii() and zip_code.isdigit() and len(zip_code) == 5): 
        return jsonify({"error": "Enter a valid 5 digit ZIP code."}), 400  

    try: 
        zip_response = requests.get(f"https:", )

    except requests.RequestException:
        return jsonify({"error": "Unable to retrieve weather alerts. Try Again."}), 502
    
    except (KeyError, IndexError, ValueError):
        return jsonify ({}), 502



if __name__ == "__main__":
    app.run(debug = os.environ.get("FLASK_DEBUG") == "1", port = 5001)

    