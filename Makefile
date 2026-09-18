up:
	docker compose up -d --build

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose run --rm api python -m fcf.scripts.seed brandkits/acme_denim.yaml

demo:
	docker compose run --rm api python -m fcf.scripts.demo --sku ACME-DNM-001

test:
	pytest -q

live-check:
	docker compose run --rm api python -m fcf.scripts.preflight
