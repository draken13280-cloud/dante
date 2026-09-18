# Fashion Content Factory v2

Multi-channel generative content pipeline for fashion brands.

- Mock-first: `MODE=mock` produces real PNG/WAV stubs and runs fashion QA (fibre, colour, claims).
- Live generation is gated separately from live publish (`ALLOW_LIVE_PUBLISH`).
- LangGraph workflow with regen downstream-closure, budgets, HITL approval, and explicit publisher capabilities.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
python -m fcf.scripts.demo --sku ACME-DNM-001
```

Docker:

```bash
cp .env.example .env
make up
make migrate
make seed
```

## Layout

See `src/fcf/` — domain, providers, agents, QA, graph, publish, API, worker.
