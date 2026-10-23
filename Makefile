.PHONY: up down logs build test seed fmt

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

seed:
	curl -s -X POST http://localhost:8000/api/demo/seed

test:
	cd backend && . .venv/bin/activate && python -m pytest -q
