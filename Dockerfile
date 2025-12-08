# Use the official Playwright image which comes with Python and browsers installed
# This avoids the long "playwright install" step and missing system dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the application using Uvicorn
# --host 0.0.0.0 is required for Docker networking
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
