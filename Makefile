dev:
	fastapi dev app/main.py --port 5500

start-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml up

clear-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml down -v

test:
	PYTHONPATH=. pytest -v unit_tests/

test-acc:
	PYTHONPATH=. pytest -v acceptance_tests/

test-all:
	PYTHONPATH=. pytest -v

deploy:
	./deploy.sh

test-docker:
	docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml up --build --exit-code-from central_v2_app_server && docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml down -v

clear-test-docker:
	docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml down -v