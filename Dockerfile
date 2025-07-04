FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the files
COPY ./app ./app
COPY .version ./.version

# Expose port
EXPOSE 5500

# Run the FastAPI app
CMD ["fastapi", "run", "app/main.py", "--port", "5500"]