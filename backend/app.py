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



