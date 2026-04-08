# Whoop Data Fetcher

Pulls all your personal Whoop data via the official API and saves it to `whoop_data.json`.

## What it fetches

- Profile & body measurements
- Cycles (daily physiological data + strain)
- Recovery (score, HRV, resting heart rate)
- Sleep (stages, performance score)
- Workouts (strain, heart rate zones, kilojoules)

All historical data is retrieved via pagination.

## Credentials

| Key | Value |
|---|---|
| Client ID | `4fe5ab37-8a78-490b-b674-61bc55682fc9` |
| Client Secret | `1d28f5d4a66c5cde0b21fd155cff9c890cad9d6b16706d8ae232866d8b0fc5cd` |
| Redirect URI | `http://localhost:8000/callback` |

Registered at https://developer.whoop.com

## Usage

```bash
WHOOP_CLIENT_ID=4fe5ab37-8a78-490b-b674-61bc55682fc9 \
WHOOP_CLIENT_SECRET=1d28f5d4a66c5cde0b21fd155cff9c890cad9d6b16706d8ae232866d8b0fc5cd \
python3 whoop_fetch.py
```

1. Visit the printed URL in your browser
2. Log in and authorize
3. Your browser will redirect to `localhost:8000` and show an error — that's expected
4. Copy the full URL from your address bar (starts with `http://localhost:8000/callback?code=...`)
5. Run again with that URL as an argument:

```bash
WHOOP_CLIENT_ID=4fe5ab37-8a78-490b-b674-61bc55682fc9 \
WHOOP_CLIENT_SECRET=1d28f5d4a66c5cde0b21fd155cff9c890cad9d6b16706d8ae232866d8b0fc5cd \
python3 whoop_fetch.py "http://localhost:8000/callback?code=..."
```

Output is saved to `whoop_data.json` in the same folder.
