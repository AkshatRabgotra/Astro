.PHONY: dev test lint docker-up docker-down

dev:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -v

docker-up:
	docker compose up --build

docker-down:
	docker compose down
