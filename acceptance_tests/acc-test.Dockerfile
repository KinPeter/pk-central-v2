FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the files
COPY ../ .

# Expose port
EXPOSE 5500

# Run the FastAPI acceptance tests
CMD ["sh", "-c", "sleep 30 && pytest -v"]