import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import config

# Suppress OTel "Failed to detach context" warning caused by generator/context interaction.
# Tracing is unaffected.
# Known bug: https://github.com/open-telemetry/opentelemetry-python/issues/2606
class _SuppressOtelDetachWarning(logging.Filter):
    def filter(self, record):
        return "Failed to detach context" not in record.getMessage()

logging.getLogger("opentelemetry.context").addFilter(_SuppressOtelDetachWarning())

from groq import Groq
from qdrant_client import QdrantClient
from fastapi.responses import JSONResponse

from ui.css import custom_css
from ui.gradio_app import create_gradio_ui


def _check_groq() -> tuple[bool, str]:
    api_key = os.getenv("GROQ_API_KEY") or ""
    if not api_key:
        return False, "Missing GROQ_API_KEY"

    try:
        client = Groq(api_key=api_key)
        client.models.list()
        return True, "Groq API key is valid"
    except Exception as exc:  # pragma: no cover - endpoint-level diagnostics
        return False, f"Groq validation failed: {exc.__class__.__name__}: {exc}"


def _check_qdrant() -> tuple[bool, str]:
    try:
        if config.QDRANT_HOST:
            client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
        else:
            client = QdrantClient(path=config.QDRANT_DB_PATH)

        client.get_collections()
        return True, "Qdrant is reachable"
    except Exception as exc:  # pragma: no cover - endpoint-level diagnostics
        return False, f"Qdrant check failed: {exc.__class__.__name__}: {exc}"


def _check_postgres() -> tuple[bool, str]:
    if not config.DATABASE_URL:
        return True, "Postgres not configured; using in-memory checkpointer"

    try:
        import psycopg

        with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True, "Postgres checkpointer is reachable"
    except Exception as exc:  # pragma: no cover - endpoint-level diagnostics
        return False, f"Postgres check failed: {exc.__class__.__name__}: {exc}"


def health_check() -> JSONResponse:
    groq_ok, groq_msg = _check_groq()
    qdrant_ok, qdrant_msg = _check_qdrant()
    postgres_ok, postgres_msg = _check_postgres()

    payload = {
        "status": "ok" if groq_ok and qdrant_ok and postgres_ok else "degraded",
        "checks": {
            "groq": {"ok": groq_ok, "message": groq_msg},
            "qdrant": {"ok": qdrant_ok, "message": qdrant_msg},
            "postgres": {"ok": postgres_ok, "message": postgres_msg},
        },
    }

    status_code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)


if __name__ == "__main__":
    if not config.APP_USERNAME or not config.APP_PASSWORD:
        raise RuntimeError(
            "APP_USERNAME and APP_PASSWORD must be set in .env before starting the app."
        )

    print("\n🔨 Creating RAG Assistant...")
    demo = create_gradio_ui()
    demo.app.add_api_route("/healthz", health_check, methods=["GET"], include_in_schema=False)
    print("\n🚀 Launching RAG Assistant...")
    demo.launch(
        css=custom_css,
        auth=(config.APP_USERNAME, config.APP_PASSWORD),
    )