.PHONY: dev prod stop restart update logs shell

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

stop:
	docker compose stop

start:
	docker compose start

restart:
	docker compose restart bot

update:
	docker compose up -d --build bot

logs:
	docker compose logs -f bot

down:
	docker compose down

shell:
	docker compose exec bot bash