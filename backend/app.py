# Flask: creates backend web apllication/server
# request: receives information from frontend (a submitted hurricane alert)
#jonsify: Converts python data to JSON response for frontend
#CORS: Allows frontend and backend to communicate
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
CORS(app, origins = allowed_origins)

MAX_ALERT_LENGTH = 5000 

@app.route("/api/health", methods = ["GET"]) 
def health():
    return jsonify({"message": "Areacane backend is running"})

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

if __name__ == "__main__":
    app.run(debug = os.environ.get("FLASK_DEBUG") == "1", port = 5001)

    