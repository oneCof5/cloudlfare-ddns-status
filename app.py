import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from datetime import datetime, timezone

SOURCE = os.environ.get("SOURCE_FILE", "/data/cf-ddns-updates.json")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
REFRESH = int(os.environ.get("REFRESH_SECONDS", "30"))
HISTORY_LIMIT = int(os.environ.get("HISTORY_LIMIT", "25"))

state = {
    "status": "starting",
    "lastScraped": None,
    "lastChanged": None,
    "currentIp": None,
    "historyCount": 0,
    "ipHistory": [],
    "sourceFile": SOURCE,
    "lastReadAt": None,
    "error": None,
}

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def pick(entry, *keys):
    for key in keys:
        if key in entry and entry[key] not in (None, ""):
            return entry[key]
    return None

def load_source():
    if not os.path.exists(SOURCE):
        return {
            "status": "waiting",
            "lastScraped": None,
            "lastChanged": None,
            "currentIp": None,
            "historyCount": 0,
            "ipHistory": [],
            "sourceFile": SOURCE,
            "lastReadAt": now_iso(),
            "error": "Source file not found yet"
        }

    try:
        with open(SOURCE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        return {
            "status": "error",
            "lastScraped": None,
            "lastChanged": None,
            "currentIp": None,
            "historyCount": 0,
            "ipHistory": [],
            "sourceFile": SOURCE,
            "lastReadAt": now_iso(),
            "error": f"Failed reading source JSON: {e}"
        }

    entries = raw if isinstance(raw, list) else [raw]
    cleaned = []

    for e in entries:
        if not isinstance(e, dict):
            continue
        item = {
            "timestamp": pick(e, "timestamp", "time", "date"),
            "ip": pick(e, "ip", "ipv4", "address"),
            "updated": pick(e, "updated", "changed"),
            "host": pick(e, "host", "domain", "hostname", "record"),
            "raw": e,
        }
        cleaned.append(item)

    current_ip = cleaned[-1]["ip"] if cleaned else None
    last_scraped = cleaned[-1]["timestamp"] if cleaned else None

    changed_entries = [x for x in cleaned if str(x["updated"]).lower() in ("true", "1", "yes")]
    last_changed = changed_entries[-1]["timestamp"] if changed_entries else None

    history = []
    for item in reversed(cleaned[-HISTORY_LIMIT:]):
        history.append({
            "timestamp": item["timestamp"],
            "ip": item["ip"],
            "updated": item["updated"],
            "host": item["host"],
        })

    return {
        "status": "ok",
        "lastScraped": last_scraped,
        "lastChanged": last_changed,
        "currentIp": current_ip,
        "historyCount": len(cleaned),
        "ipHistory": history,
        "sourceFile": SOURCE,
        "lastReadAt": now_iso(),
        "error": None,
    }

def updater():
    global state
    while True:
        state = load_source()
        time.sleep(REFRESH)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/status.json"):
            payload = json.dumps(state, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    Thread(target=updater, daemon=True).start()
    HTTPServer((HOST, PORT), Handler).serve_forever()