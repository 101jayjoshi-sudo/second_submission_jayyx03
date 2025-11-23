# Swing Reversion Bot - Dockerfile
FROM python:3.11-slim

LABEL description="Swing Reversion Grid Strategy"
LABEL strategies="swing_reversion"

# Set working directory
WORKDIR /app

# Copy base bot infrastructure
COPY base-bot-template/ /app/base/

# Copy Strategy-specific files
COPY swing-reversion-strategy/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r /app/base/requirements.txt
# Also install local requirements if any
RUN if [ -f /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi

# Make startup script executable
RUN chmod +x /app/startup.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 3010

# Default environment
ENV BOT_EXCHANGE=paper
ENV BOT_STRATEGY=swing_reversion
ENV BOT_SYMBOL=BTC-USD
ENV BOT_STARTING_CASH=10000.0
ENV BOT_SLEEP=60

# Start the bot
CMD ["python", "/app/startup.py"]
