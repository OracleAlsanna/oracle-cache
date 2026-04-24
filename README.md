# Oracle Cache

Part 5 of 5 — the final layer of the Oracle URL shortener platform. Extends Part 4 (oracle-analytics) with Redis caching for fast redirects and rate limiting to prevent abuse.

## Series Roadmap

| Part | Project | Description |
|------|---------|-------------|
| 1 | oracle-core | Core URL shortener — shorten, list, delete, redirect |
| 2 | oracle-frontend | React + Vite frontend for oracle-core |
| 3 | oracle-clicks | Click tracking — logs referrer and user-agent on every redirect |
| 4 | oracle-analytics | Analytics endpoints — click counts, per-link history, recent clicks |
| 5 | **oracle-cache** | **Redis caching for redirects + rate limiting** |

## What's New in Part 5

- **Redis cache** — `/{code}` checks Redis before hitting SQLite. Cache TTL is 1 hour. Deleted links are immediately evicted.
- **Rate limiting** — sliding window counters stored in Redis, scoped per IP per endpoint.
- **Graceful degradation** — if Redis is not running, redirects fall back to SQLite and rate limiting is skipped. The API never returns 500 due to Redis being down.

## Setup

### Prerequisites

- Python 3.10+
- Redis running locally

### Start Redis

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# or run in the foreground
redis-server
```

Verify Redis is up:

```bash
redis-cli ping
# PONG
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the server

```bash
uvicorn main:app --reload
```

The API starts at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## Redis notes

- Redis must be running for caching and rate limiting to be active.
- Without Redis the API runs in degraded mode: all redirects hit SQLite, rate limiting is skipped, and no errors are surfaced to the client.
- Cache keys use the prefix `url:` (e.g. `url:AB12`).
- Rate limit keys use the prefix `rl:` (e.g. `rl:127.0.0.1:redirect`).

## Endpoints

### Links

| Method | Path | Description | Rate limit |
|--------|------|-------------|------------|
| `POST` | `/links` | Shorten a URL | 20/min per IP |
| `GET` | `/links` | List all links | — |
| `GET` | `/links/{name}` | Get a single link | — |
| `DELETE` | `/links/{name}` | Delete a link (also evicts cache) | — |

**POST /links** request body:
```json
{ "url": "https://example.com" }
```

**POST /links** response:
```json
{ "name": "AB12", "url": "https://example.com" }
```

### Redirect

| Method | Path | Description | Rate limit |
|--------|------|-------------|------------|
| `GET` | `/{code}` | Redirect to original URL | 60/min per IP |

Checks Redis first. On a cache miss, looks up SQLite and writes the result to Redis with a 1-hour TTL. Click is logged asynchronously in both cases.

### Analytics

| Method | Path | Description | Rate limit |
|--------|------|-------------|------------|
| `GET` | `/analytics` | All links with click counts | 30/min per IP |
| `GET` | `/analytics/recent` | 50 most recent clicks | — |
| `GET` | `/analytics/{code}` | Full analytics for one link | — |

### Rate limit response

When a limit is exceeded the API returns HTTP 429:

```json
{ "detail": "Too many requests. Please slow down." }
```

## Database

Uses the same SQLite database as all prior parts: `~/.oracle/db.sqlite3`. No migration needed when upgrading from Part 4.
