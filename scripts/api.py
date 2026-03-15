from flask import Flask, jsonify, request
import subprocess
import sys
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON = sys.executable

@app.route("/scrape", methods=["POST"])
def scrape():
    team = request.json.get("team", "Arsenal FC")
    result = subprocess.run(
        [PYTHON, os.path.join(BASE_DIR, "scripts", "scraper.py"), team],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )
    return jsonify({
        "status": "ok" if result.returncode == 0 else "error",
        "output": result.stdout,
        "error": result.stderr
    })

@app.route("/ingest", methods=["POST"])
def ingest():
    result = subprocess.run(
        [PYTHON, os.path.join(BASE_DIR, "scripts", "ingest.py")],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )
    return jsonify({
        "status": "ok" if result.returncode == 0 else "error",
        "output": result.stdout,
        "error": result.stderr
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(port=5050, debug=True)