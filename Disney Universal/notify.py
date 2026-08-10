#!/usr/bin/env python3
"""Send a Pushover notification. Usage: notify.py "Title" "Message" [url]"""
import json
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
creds = json.loads((HERE / "pushover_creds.json").read_text())

title = sys.argv[1] if len(sys.argv) > 1 else "Trip bot"
message = sys.argv[2] if len(sys.argv) > 2 else "(no message)"
data = {"token": creds["api_token"], "user": creds["user_key"],
        "title": title, "message": message[:1000]}
if len(sys.argv) > 3:
    data["url"] = sys.argv[3]

req = urllib.request.Request(
    "https://api.pushover.net/1/messages.json",
    data=urllib.parse.urlencode(data).encode(),
    headers={"User-Agent": "Trips-notify/1.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("sent" if r.status == 200 else f"failed: {r.status}")
