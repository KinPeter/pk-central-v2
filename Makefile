dev:
	fastapi dev app/main.py --port 5500

start-db:
	docker-compose -f dev-db/dev-db.docker-compose.yml up

clear-db:
	docker-compose -f dev-db/dev-db.docker-compose.yml down -v

deploy:
	./deploy.sh
