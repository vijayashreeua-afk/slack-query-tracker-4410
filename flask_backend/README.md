# Flask Backend - Slack Query Tracker

This backend provides APIs to store, fetch, and export Slack query items, and to configure the Slack channel. It integrates with Slack using a bot token and persists data using a simple JSON storage backend.

## Requirements

- Python 3.10+
- pip

## Setup

1. Create and populate your environment file:

```
cp .env.example .env
```

Edit `.env` to set:
- FLASK_ENV=development
- PORT=5000
- FRONTEND_ORIGIN=http://localhost:3000
- SLACK_BOT_TOKEN=your-bot-token
- STORAGE_BACKEND=json
- STORAGE_FILE=slack-query-tracker-4410/flask_backend/data/queries.json

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Run the server:

```
python app.py
```

Server runs by default on `http://localhost:5000`.

CORS is configured to allow the origin set in `FRONTEND_ORIGIN` for paths under `/api/*`.

## API

- GET /api/health
  - Simple health check

- GET /api/config/channel
  - Response: `{ channel_id, channel_name, valid }`

- POST /api/config/channel
  - Body: `{ channel_id | channelId, channel_name | channelName }`
  - Validates channel via Slack (if token configured) and persists

- GET /api/queries?status=&page=&pageSize=&search=
  - Response: `{ items, total }`

- POST /api/queries
  - Body: `{ user, thread_url, resolver?, status? }`
  - Response: created item

- PATCH /api/queries/<id>
  - Body: partial fields `{ resolver?, status?, resolved_at? }`
  - Sets `resolved_at` automatically when moving to `resolved` if not provided

- DELETE /api/queries/<id>
  - Response: `{ ok: true }`

- POST /api/slack/fetch
  - Uses channel from saved config and bot token to pull recent messages
  - Applies heuristic: message has a thread and contains `?` or `help`
  - Upserts entries by thread permalink

- POST /api/export
  - Returns an Excel file (xlsx) containing current queries

## Notes

- Storage is JSON-based by default and safe for local development. For production, you can extend `storage.py` with a different backend and switch using `STORAGE_BACKEND`.

- Slack permissions:
  - `channels:history` or `conversations.history`
  - `users:read`
  - `channels:read` or `conversations.read`

- Excel is generated using `openpyxl` and delivered with appropriate headers.

```text
Models
- ChannelConfig: { channel_id, channel_name }
- QueryItem: { id, user, thread_url, resolver, status, created_at, resolved_at }
```
