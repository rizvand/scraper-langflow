FROM langflowai/langflow:latest

USER root

RUN mkdir /app/flows
COPY ./flows/*.json /app/flows/
ENV LANGFLOW_LOAD_FLOWS_PATH=/app/flows

ENV LANGFLOW_VARIABLES_TO_GET_FROM_ENVIRONMENT="GOOGLE_API_KEY"
ENV GOOGLE_API_KEY=<replace-with-your-google-api-key>

RUN apt-get update \
 && apt-get install -y chromium --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

# Install pip in the virtual environment
RUN /app/.venv/bin/python -m ensurepip --upgrade

# Install the zendriver module using the pip from the virtual environment
RUN /app/.venv/bin/python -m pip install zendriver

# Set the environment variable to use the virtual environment's Python by default
ENV PATH="/app/.venv/bin:$PATH"

# Set Chrome binary path for zendriver
ENV CHROME_BIN=/usr/bin/google-chrome-stable

CMD ["python", "-m", "langflow", "run", "--host", "0.0.0.0", "--port", "7860"]