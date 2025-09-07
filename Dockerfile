FROM langflowai/langflow:latest

USER root

RUN mkdir /app/flows
COPY ./flows/*.json /app/flows/
ENV LANGFLOW_LOAD_FLOWS_PATH=/app/flows

ENV LANGFLOW_VARIABLES_TO_GET_FROM_ENVIRONMENT="OPENAI_API_KEY"
ENV OPENAI_API_KEY=<your_api_key>

RUN apt-get update \
 && apt-get install -y chromium xvfb git --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Clone and setup stealth-browser-mcp with retry logic
RUN for i in 1 2 3; do \
    git clone https://github.com/vibheksoni/stealth-browser-mcp.git /app/stealth-browser-mcp && break || \
    (echo "Attempt $i failed, retrying..." && sleep 5); \
    done
WORKDIR /app/stealth-browser-mcp
RUN /app/.venv/bin/python -m venv mcp-venv
RUN /app/stealth-browser-mcp/mcp-venv/bin/pip install -r requirements.txt

# Return to app directory
WORKDIR /app

# Set environment variables to disable timeouts
ENV LANGFLOW_REQUEST_TIMEOUT=0
ENV LANGFLOW_WORKER_TIMEOUT=0
ENV LANGFLOW_BACKEND_TIMEOUT=0

# Start virtual display and run langflow
CMD ["sh", "-c", "Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp & python -m langflow run --host 0.0.0.0 --port 7860 --worker-timeout 0"]