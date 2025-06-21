# PK Central API v2

A collection of API endpoints to support multiple hobby projects powered by Python and FastAPI.

## Features

- **Feature** Important feature TBA

## Technologies used

- Python with FastAPI
- Pydantic
- MongoDB with PyMongo
- Docker and Docker-compose
- Unit tests with pytest and unittest
- Acceptance tests with pytest, respx and Starlette

## 3rd party APIs and SDKs

- Google Gemini GenAI SDK
- Reddit SDK (AsyncPraw)
- Strava API
- DeepL API
- LocationIQ API
- AirLabs API

## Setup and run locally

1. Install Python 3.13.x and set up the virtual environment.

   ```bash
   pyenv install 3.13.3
   pyenv local 3.13.3
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment variables into the `.env` file, see all required variables in the `.env.example` file.

## API

Dev database:

```bash
# Start the db in Docker:
make start-db

# Clear the db container and volumes:
make clear-db
```

Run in local:

```bash
make dev
```

Open your browser:

- Swagger UI Api docs: `http://localhost:5500/docs`
- Redocly Api docs: `http://localhost:5500/redoc`

Publish new docker image:

```bash
make deploy
```

## Testing

### Unit tests

Unit tests are using the `pytest` and `unittest` libraries and can be found under the `unit_tests/` folder.

Run the unit tests with:

```bash
make test
```

### Acceptance tests

Acceptance tests are using the `pytest`, `respx` and `Starlette` libraries and can be found under the `acceptance_tests/` folder.

Run the acceptance tests with:

```bash
make test-acc
```

Note: The acceptance tests require a running dev database, so make sure to run `make start-db` before running the acceptance tests.

### Running all tests

Run all tests locally with:

```bash
make test-all
```

Run all tests in docker with:

```bash
make test-docker
```

Using Docker for testing is recommended, as it ensures a clean environment and avoids issues with local dependencies. It also has a separate MongoDB instance for testing purposes.

In case of failure you have to manually clear the docker volumes:

```bash
make clear-test-docker
```
