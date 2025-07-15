# ===
# Running the development server
# ===
dev:
	fastapi dev app/main.py --port 5500

# ===
# Running the development DB in docker
# ===
start-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml up

clear-db:
	docker-compose -f dev_db/dev-db.docker-compose.yml down -v

# ===
# Testing with pytest
# ===
test:
	PYTHONPATH=. pytest -v unit_tests/

test-acc:
	PYTHONPATH=. pytest -v acceptance_tests/

test-all:
	PYTHONPATH=. pytest -v

# ===
# Testing in Docker
# ===
test-docker:
	docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml up --build --exit-code-from central_v2_app_server && docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml down -v

clear-test-docker:
	docker-compose -f ./acceptance_tests/acc-test.docker-compose.yml down -v

# ===
# Building the Docker image and publishing to Docker Hub
# ===
deploy:
	./deploy.sh

# ===
# Seeding and backups
# Run a seed script for initial V2 data. Needs the FILE variable e.g. `make seed-init-v2 FILE=static_data`
# ===
seed-init-v2:
	PYTHONPATH=. python local/seed_init_v2/seed_$(FILE).py

# Run a seed script for V1 backup data. Needs the FILE variable e.g. `make seed-v1 FILE=activities`
seed-v1:
	PYTHONPATH=. python local/seed_v1_backup/seed_$(FILE).py