# Use a slim Python base image
FROM python:3.11-slim-buster
 
# Set the working directory
WORKDIR /app
 
# Install dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
 
 
COPY requirements.txt /app/
RUN pip install -r requirements.txt
 
# Copy the application code
COPY . /app/
 
# Expose the application port
EXPOSE 8000
 
# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
 