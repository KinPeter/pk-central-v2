# PK Central API v2

Describe the API here.

## Features

- **Feature** Important feature TBA

## Technologies used

- Python with FastAPI
- Pydantic
- MongoDB
- Strava API
- Docker with Docker-compose

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
