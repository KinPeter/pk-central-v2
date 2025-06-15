dev:
	fastapi dev app/main.py --port 5500

start-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml up

clear-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml down -v

test:
	PYTHONPATH=. pytest -v

deploy:
	./deploy.sh
