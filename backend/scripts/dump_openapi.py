"""Dump the FastAPI OpenAPI schema to disk.

The generated schema is the source of truth for the frontend's API client
(see Makefile `gen-api` target). Running this script does NOT start a server
— FastAPI builds the schema purely from registered routes / Pydantic models.

Usage:
    python -m scripts.dump_openapi              # writes ../frontend/openapi.json
    python -m scripts.dump_openapi --output X   # writes X
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Importing `app.main` triggers route registration. We avoid running the
# lifespan (which would try to load the trained models from disk).
from app.main import app

DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "openapi.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Where to write the schema (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    schema = app.openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI schema -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
