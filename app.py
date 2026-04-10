import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from datetime import datetime, timezone

SOURCE = os.environ.get("SOURCE_FILE") or "/data/cf-ddns-updates.json"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
REFRESH = int(os.environ.get("REFRESH_SECONDS", "30"))

state = {
    "status": "starting",
    "lastScraped": None,
    "lastChanged": None,
    "currentIp": None,
    "recordId": None,
    "recordName": None,
    "recordType": None,
    "historyCount": 0,
    "ipHistory": [],
    "sourceFile": SOURCE,
    "lastReadAt": None,
    "error": None,
}

previous_ip = None
ip_history = []

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def load_source():
    global previous_ip, ip_history

    if not os.path.exists(SOURCE):
        return {
            "status": "waiting",
            "lastScraped": None,
            "lastChanged": None,
            "currentIp": None,
            "recordId": None,
            "recordName": None,
            "recordType": None,
            "historyCount": len(ip_history),
            "ipHistory": ip_history[-25:],
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
            "recordId": None,
            "recordName": None,
            "recordType": None,
            "historyCount": len(ip_history),
            "ipHistory": ip_history[-25:],
            "sourceFile": SOURCE,
            "lastReadAt": now_iso(),
            "error": f"Failed reading source JSON: {e}"
        }

    if not isinstance(raw, dict):
        return {
            "status": "error",
            "lastScraped": None,
            "lastChanged": None,
            "currentIp": None,
            "recordId": None,
            "recordName": None,
            "recordType": None,
            "historyCount": len(ip_history),
            "ipHistory": ip_history[-25:],
            "sourceFile": SOURCE,
            "lastReadAt": now_iso(),
            "error": "Expected a single JSON object"
        }

    current_ip = raw.get("content")
    scraped_at = now_iso()
    changed_at = None

    if current_ip and current_ip != previous_ip:
        changed_at = scraped_at
        ip_history.append({
            "timestamp": scraped_at,
            "ip": current_ip
        })
        previous_ip = current_ip

    return {
        "status": "ok",
        "lastScraped": scraped_at,
        "lastChanged": changed_at,
        "currentIp": current_ip,
        "recordId": raw.get("id"),
        "recordName": raw.get("name"),
        "recordType": raw.get("type"),
        "historyCount": len(ip_history),
        "ipHistory": list(reversed(ip_history[-25:])),
        "sourceFile": SOURCE,
        "lastReadAt": scraped_at,
        "error": None,
    }

def updater():
    global state
    last_changed_persist = None

    while True:
        new_state = load_source()

        if new_state.get("lastChanged"):
            last_changed_persist = new_state["lastChanged"]
        elif last_changed_persist:
            new_state["lastChanged"] = last_changed_persist

        state = new_state
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