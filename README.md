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

3. Set up the environment variables into the `.env` file.

   ```bash
   # Mongo DB connection string and database name
   MONGODB_URI=
   MONGODB_NAME=

   # Root path on the server where the script is running
   ROOT_PATH=

   # TBA

   ```

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

- Api docs: `http://localhost:5500/docs`

Publish new docker image:

```bash
make deploy
```
