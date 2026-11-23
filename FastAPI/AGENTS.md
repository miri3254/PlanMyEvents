# FastAPI agent instructions
Read `../AGENTS.md` and shared knowledge under `../Angular/.ai/`.
Active chain: routers -> services -> repositories/models, with Pydantic contracts in schemas.
Use `app/db/base.py`, `app/db/engine.py`, `app/db/session.py` as the active database wiring traced from main.py.
Calculation engine: `app/services/event_calculation_service.py`; event price/stock/shopping integration: `app/services/event_service.py`.
PDF implementation: `app/utils/pdf_generator.py`, assembled by `app/routers/events.py`.
Read schemas and frontend mappings together when changing fields. Schema changes need a reviewed Alembic migration.
Use an isolated DATABASE_URL before tests/importing app; lifespan performs writes outside dependency overrides.
Do not run populate_db.py, clear_db_runner.py or other mutation helpers on the business database as setup.
Run focused pytest tests with the existing .venv interpreter when available. A static documentation task does not require starting the server.
