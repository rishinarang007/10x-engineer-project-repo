FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8000

# Run without reload for production
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
