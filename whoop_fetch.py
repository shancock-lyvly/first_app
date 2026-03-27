#!/usr/bin/env python3
"""
Whoop data fetcher — pulls all personal data via OAuth 2.0 and saves to whoop_data.json
"""

import json
import os
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

CLIENT_ID = os.environ["WHOOP_CLIENT_ID"]
CLIENT_SECRET = os.environ["WHOOP_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "offline read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE = "https://api.prod.whoop.com/developer/v1"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorized! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code parameter.")

    def log_message(self, format, *args):
        pass  # suppress request logs


def get_auth_code():
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
    })
    url = f"{AUTH_URL}?{params}"
    print(f"\nOpening browser for Whoop authorization...")
    print(f"If it doesn't open automatically, visit:\n  {url}\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", 8000), CallbackHandler)
    thread = Thread(target=server.handle_request)
    thread.start()
    thread.join(timeout=120)
    server.server_close()

    if not auth_code:
        raise RuntimeError("No authorization code received within 2 minutes.")
    return auth_code


def get_token(code):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def api_get(token, path, params=None):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all(token, path):
    records = []
    params = {"limit": 25}
    while True:
        resp = api_get(token, path, params)
        records.extend(resp.get("records", []))
        next_token = resp.get("next_token")
        if not next_token:
            break
        params["nextToken"] = next_token
    return records


def main():
    code = get_auth_code()
    print("Got authorization code, exchanging for token...")
    token_data = get_token(code)
    token = token_data["access_token"]
    print("Authenticated.\n")

    print("Fetching profile...")
    profile = api_get(token, "/user/profile/basic")

    print("Fetching body measurements...")
    body = api_get(token, "/user/measurement/body")

    print("Fetching cycles...")
    cycles = fetch_all(token, "/cycle")
    print(f"  {len(cycles)} cycles")

    print("Fetching recoveries...")
    recoveries = fetch_all(token, "/recovery")
    print(f"  {len(recoveries)} recoveries")

    print("Fetching sleeps...")
    sleeps = fetch_all(token, "/activity/sleep")
    print(f"  {len(sleeps)} sleep records")

    print("Fetching workouts...")
    workouts = fetch_all(token, "/activity/workout")
    print(f"  {len(workouts)} workouts")

    data = {
        "profile": profile,
        "body": body,
        "cycles": cycles,
        "recoveries": recoveries,
        "sleeps": sleeps,
        "workouts": workouts,
    }

    output_path = "whoop_data.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nDone! Data saved to {output_path}")
    print(f"  Cycles:     {len(cycles)}")
    print(f"  Recoveries: {len(recoveries)}")
    print(f"  Sleeps:     {len(sleeps)}")
    print(f"  Workouts:   {len(workouts)}")


if __name__ == "__main__":
    main()
