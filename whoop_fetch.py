#!/usr/bin/env python3
"""
Whoop data fetcher — pulls all personal data via OAuth 2.0 and saves to whoop_data.json
"""

import json
import os
import urllib.parse
import urllib.request

CLIENT_ID = os.environ["WHOOP_CLIENT_ID"]
CLIENT_SECRET = os.environ["WHOOP_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "offline read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
API_BASE = "https://api.prod.whoop.com/developer/v1"


def print_auth_url():
    params = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
    })
    url = f"{AUTH_URL}?{params}"
    print(f"\n1. Visit this URL in your browser:\n\n  {url}\n")
    print("2. Log in and authorize the app.")
    print("3. You'll be redirected to localhost:8000 (it will fail to load — that's OK).")
    print("4. Copy the FULL URL from your browser's address bar.")
    print(f"\n5. Then run:  python3 whoop_fetch.py <paste-full-url-here>\n")


def extract_code_from_redirect(redirect_url):
    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)
    if "code" not in params:
        raise RuntimeError("No 'code' found in the URL.")
    return params["code"][0]


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
    import sys
    if len(sys.argv) < 2:
        print_auth_url()
        return

    code = extract_code_from_redirect(sys.argv[1])
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
