# Revenue Pipeline Monitor

Stripe → HubSpot synchronization pipeline with OAuth 2.0, HMAC-verified webhooks, idempotency, retry & rate limiting, and LLM enrichment via Anthropic Claude function calling.

## Stack

- **API & Async:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, httpx, slowapi, tenacity
- **Data & Migrations:** PostgreSQL, SQLAlchemy (asyncio + asyncpg), Alembic
- **Queue & Cache:** Celery, Redis
- **AI Enrichment:** Anthropic Python SDK (Claude)
- **Testing & Quality:** pytest, pytest-asyncio, pytest-cov, ruff

## Project Structure

```
app/          Application code (API, services, models, workers)
migrations/   Alembic database migrations
tests/        Automated test suite (pytest)
postman/      Postman collection
docker/       Container configuration
scripts/      Utility scripts
```

## Local Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for local setup without Docker (PostgreSQL, synchronous Celery mode, uvicorn --reload) and [PHASES.md](PHASES.md) for the implementation phases.

## License

MIT — see [LICENSE](LICENSE).