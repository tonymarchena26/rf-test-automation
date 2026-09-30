# One image for the simulator, the dashboard and the test runner.
FROM python:3.12-slim

# Chromium + its driver so Selenium can run headless inside the container
RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER=/usr/bin/chromedriver \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies first: Docker caches this layer, rebuilds are fast
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command: run the whole test suite
CMD ["pytest"]
