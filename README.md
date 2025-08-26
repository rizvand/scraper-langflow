# Langflow Scraper Chatbot

A complete setup for running a web scraping chatbot powered by Langflow with a FastAPI backend and an HTML frontend. The chatbot can scrape websites, extract data, and provide responses with both human-readable text and structured JSON content.

## Features

- **Langflow Integration**: Flow-based AI agent for web scraping
- **Zendriver Support**: Advanced browser automation with Chrome/Chromium for dynamic content scraping
- **FastAPI Backend**: RESTful API to interact with Langflow flows
- **Web Interface**: HTML chatbot interface with JSON data display

## AI Model API Keys Setup

### 1. Google API Key (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable required APIs (e.g., Custom Search API, Places API)
4. Navigate to "Credentials" section
5. Click "Create Credentials" → "API Key"
6. Copy the API key
7. Add to your environment or Dockerfile

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Google API key (required for the AI agent)

### Setup

1. **Clone and navigate to the project:**

   ```bash
   cd scraper-langflow
   ```
2. **Configure API keys in Dockerfile:**

   Edit the `Dockerfile` and add your Google API keys:

   ```dockerfile
   ENV GOOGLE_API_KEY=your-google-api-key-here
   ```
3. **Build and start the services:**

   ```bash
   docker-compose up --build -d
   ```
4. **Access the applications:**

   - **Chatbot Interface**: http://localhost:8000
   - **Langflow UI**: http://localhost:7860
   - **FastAPI Docs**: http://localhost:8000/docs
5. **Manual Setup for Langflow**

   - Open Langflow UI (http://localhost:7860)
   - Navigate to your project (e.g., "Starter Project")
   - Navigate to MCP Server > JSON
   - Copy MacOS/Linux MCP Server JSON Config
   - Go to Flows > [main] scraper agent
   - Inside MCP Tools, click on MCP Server > + Add MCP Server > Paste in JSON Config > Add Server
   - In the Agent component, make sure to use `gemini-2.5-flash` model
6. **Get your Flow ID:**

   - Open Langflow UI (http://localhost:7860)
   - Navigate to your project (e.g., "Starter Project")
   - Copy the Flow ID from the URL or flow settings
   - Example: `93f59fc7-5ea5-439c-ab7b-9520b3423a6d`
7. **Get your Langflow API Key:**

   * Access your Langflow instance (http://localhost:7860)
   * Go to "Settings" or "API Keys" section
   * Generate a new API key
   * Copy the generated key
   * Use this key in the chatbot interface or API requests
8. **Start chatting:**

   - Enter your Flow ID and Langflow API Key in the web interface
   - Begin chatting with your scraping agent!

## Services

### Langflow (Port 7860)

- AI flow builder and execution engine
- Web scraping agent with multiple tools
- Flows automatically loaded from `/flows` directory

### FastAPI (Port 8000)

- RESTful API backend
- Serves the chatbot web interface
- Handles communication with Langflow
- Health monitoring endpoint

### PostgreSQL (Port 5432)

- Database for Langflow data persistence
- Automatic initialization and configuration

## API Endpoints

### FastAPI Endpoints

- `GET /` - Chatbot web interface
- `POST /chat` - Send message to chatbot
- `GET /health` - Service health check
- `GET /docs` - API documentation (Swagger UI)

### Chat API Usage

```bash
# Send a message to the chatbot
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Please scrape the latest news from example.com",
       "session_id": "my-session-123",
       "flow_id": "langflow-flow-id",
       "api_key": "your-langflow-api-key"
     }'
```

**Request Parameters:**

- `message` (required): The message to send to the chatbot
- `session_id` (optional): Session identifier for conversation continuity
- `flow_id` (required): Langflow Flow ID to execute
- `api_key` (required): Langflow API key for authentication

Response:

```json
{
  "response": "{\"text\": \"I found the latest news from example.com\", \"content\": {\"title\": \"Breaking News\", \"articles\": [{\"headline\": \"Major Update\", \"url\": \"https://example.com/news1\"}]}}",
  "session_id": "my-session-123"
}
```

**Response Format:**
The chatbot returns responses in JSON string format containing:

- `text`: Human-readable response message
- `content`: Structured data (scraped content, extracted information, etc.)

### Debug Endpoints

- `GET /debug/flows?api_key=your-key` - List available projects and flows
- `POST /debug/test-flow?flow_id=your-flow-id&api_key=your-key` - Test a specific flow

## Development

### Project Structure

```
scraper-langflow/
├── app.py                 # FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Langflow container with API keys
├── Dockerfile.fastapi    # FastAPI container
├── docker-compose.yml    # Multi-service setup
├── static/
│   └── index.html        # Chatbot web interface with JSON display
└── flows/                # Langflow flow definitions
    ├── [main] scraper agent.json
    └── subflow - scraper tool.json
```

### Customization

1. **Modify Flows**: Edit JSON files in `/flows` directory
2. **Update UI**: Customize `static/index.html`
3. **Extend API**: Add endpoints in `app.py`
4. **Environment**: Update `.env` for configuration

### Debugging

View logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f langflow
docker-compose logs -f fastapi
```

## Troubleshooting

### Common Issues

1. **"No flow_id provided" error**:

   - Enter a valid Flow ID in the web interface
   - Or set `FLOW_ID` environment variable in Dockerfile
2. **API authentication errors**:

   - Verify your Langflow API key is correct
   - Check if Langflow requires authentication for your setup
3. **Langflow not connecting**:

   - Check if all services are running with `docker-compose ps`
   - Verify Langflow is accessible at http://localhost:7860
4. **Invalid OpenAI API key**:

   - Ensure valid OpenAI API key is set in Dockerfile
   - Check API key has sufficient credits/permissions
5. **Port conflicts**:

   - Modify ports in `docker-compose.yml` if needed
   - Default ports: 8000 (FastAPI), 7860 (Langflow), 5432 (PostgreSQL)
6. **Flow execution errors**:

   - Check Langflow UI to ensure flows are loaded properly
   - Verify flow ID matches exactly (case-sensitive)

### Health Check

Visit http://localhost:8000/health to check service status:

- FastAPI server health
- Langflow connection status
- Configuration details

### Getting Flow IDs

1. Open Langflow UI: http://localhost:7860
2. Navigate to your project
3. Open the desired flow
4. Copy the Flow ID from the URL or flow settings
5. Flow IDs look like: `93f59fc7-5ea5-439c-ab7b-9520b3423a6d`

## Web Interface Features

The chatbot web interface includes several advanced features:

### JSON Response Display

- **Text Responses**: Human-readable messages displayed in chat bubbles
- **JSON Content**: Structured data displayed in formatted code blocks
- **Copy to Clipboard**: One-click copying of JSON data with visual feedback

### Configuration

- **Flow ID Input**: Required field to specify which Langflow flow to execute
- **API Key Input**: Optional field for Langflow API authentication
- **Session Management**: Automatic session ID generation for conversation continuity

### Response Format

The bot expects responses in this JSON format:

```json
{
  "text": "I scraped the website successfully!",
  "content": {
    "title": "Page Title",
    "data": ["item1", "item2", "item3"],
    "url": "https://example.com"
  }
}
```
