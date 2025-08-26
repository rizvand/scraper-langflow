from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import httpx
import json
import logging
from typing import Dict, Any, Optional
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Langflow Chatbot API", description="FastAPI server to interact with Langflow flows")

# Configuration
LANGFLOW_BASE_URL = os.getenv("LANGFLOW_BASE_URL", "http://langflow:7860")
LANGFLOW_API_KEY = os.getenv("LANGFLOW_API_KEY", "")  # Required for API authentication
FLOW_ID = os.getenv("FLOW_ID", "")  # Will be set once we get the flow ID from Langflow

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    api_key: Optional[str] = None  # Optional API key for Langflow authentication
    flow_id: Optional[str] = None  # Optional flow ID to use instead of discovery

class ChatResponse(BaseModel):
    response: str
    session_id: str

def build_langflow_headers(user_api_key: Optional[str] = None) -> Dict[str, str]:
    """
    Build headers for Langflow API requests.
    Prioritizes user-provided API key over environment variable.
    """
    headers = {"Accept": "application/json"}
    # Use user-provided API key first, fallback to environment variable
    api_key = user_api_key or LANGFLOW_API_KEY
    if api_key:
        headers["x-api-key"] = api_key
    return headers

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML chatbot interface"""
    return FileResponse('/app/static/index.html')

@app.post("/chat", response_model=ChatResponse)
async def chat_with_langflow(request: ChatRequest):
    """
    Send a message to the Langflow flow and return the response
    """
    try:
        # Prepare the request payload for Langflow API
        langflow_payload = {
            "input_value": request.message,
            "output_type": "chat",
            "input_type": "chat",
        }
        
        # Add tweaks if needed (for specific flow configuration)
        tweaks = {
            "ChatInput-C9Ir0": {},  # ChatInput component
            "Agent-OFaEi": {},      # Agent component  
            "ChatOutput-lKmkj": {}  # ChatOutput component
        }
        
        langflow_payload["tweaks"] = tweaks
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Use user-provided flow_id, fallback to environment variable
            flow_id = request.flow_id or FLOW_ID
            
            if not flow_id:
                raise HTTPException(
                    status_code=400, 
                    detail="No flow_id provided in request and no FLOW_ID environment variable set. Please provide flow_id in the request body."
                )
            
            # Make the request to Langflow
            langflow_url = f"{LANGFLOW_BASE_URL}/api/v1/run/{flow_id}"
            logger.info(f"Making request to Langflow: {langflow_url}")
            logger.info(f"Payload: {json.dumps(langflow_payload, indent=2)}")
            
            # Prepare headers with API key and content type
            run_headers = build_langflow_headers(request.api_key)
            run_headers["Content-Type"] = "application/json"
            
            response = await client.post(
                langflow_url,
                json=langflow_payload,
                headers=run_headers
            )
            
            logger.info(f"Langflow response status: {response.status_code}")
            logger.info(f"Langflow response headers: {dict(response.headers)}")
            logger.info(f"Langflow response: {response.text}")
            
            if response.status_code == 200:
                # Check if response is empty
                response_text = response.text.strip()
                if not response_text:
                    logger.error("Empty response from Langflow")
                    raise HTTPException(status_code=502, detail="Empty response from Langflow")
                
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Raw response: {repr(response.text)}")
                    raise HTTPException(status_code=502, detail=f"Invalid JSON response from Langflow: {str(e)}")
                
                logger.info(f"Parsed response data: {json.dumps(response_data, indent=2)}")
                
                # Extract the actual response text from Langflow's response
                # The structure may vary, so we'll try different possible paths
                bot_response = "I received your message but couldn't generate a proper response."
                
                # Try different response structures
                if "outputs" in response_data:
                    for output in response_data["outputs"]:
                        if "outputs" in output and output["outputs"]:
                            for output_item in output["outputs"]:
                                if "results" in output_item:
                                    results = output_item["results"]
                                    if isinstance(results, dict):
                                        if "message" in results:
                                            message_obj = results["message"]
                                            if isinstance(message_obj, dict) and "text" in message_obj:
                                                bot_response = message_obj["text"]
                                                break
                                            elif isinstance(message_obj, str):
                                                bot_response = message_obj
                                                break
                                        elif "text" in results:
                                            bot_response = results["text"]
                                            break
                                    elif isinstance(results, str):
                                        bot_response = results
                                        break
                
                # Fallback: try to find any text content in the response
                if bot_response == "I received your message but couldn't generate a proper response.":
                    def extract_text_recursively(obj):
                        if isinstance(obj, dict):
                            for key, value in obj.items():
                                if key in ["text", "content", "response", "output"] and isinstance(value, str) and value.strip():
                                    return value
                                result = extract_text_recursively(value)
                                if result:
                                    return result
                        elif isinstance(obj, list):
                            for item in obj:
                                result = extract_text_recursively(item)
                                if result:
                                    return result
                        return None
                    
                    extracted_text = extract_text_recursively(response_data)
                    if extracted_text:
                        bot_response = extracted_text
                
                return ChatResponse(response=bot_response, session_id=request.session_id)
            else:
                logger.error(f"Langflow API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Langflow API error: {response.text}"
                )
                
    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Could not connect to Langflow: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{LANGFLOW_BASE_URL}/health")
            langflow_healthy = response.status_code == 200
    except:
        langflow_healthy = False
    
    return {
        "status": "healthy",
        "langflow_connection": "connected" if langflow_healthy else "disconnected",
        "langflow_url": LANGFLOW_BASE_URL
    }

@app.get("/debug/flows")
async def debug_flows(api_key: Optional[str] = None):
    """Debug endpoint to check Langflow projects and flows"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Prepare headers with API key (user-provided or from environment)
            headers = build_langflow_headers(api_key)
            
            # Get projects
            projects_response = await client.get(
                f"{LANGFLOW_BASE_URL}/api/v1/projects",
                headers=headers
            )
            
            return {
                "status_code": projects_response.status_code,
                "headers": dict(projects_response.headers),
                "data": projects_response.json() if projects_response.status_code == 200 else None,
                "raw_text": projects_response.text[:1000] + "..." if len(projects_response.text) > 1000 else projects_response.text,
                "langflow_url": LANGFLOW_BASE_URL
            }
    except Exception as e:
        return {
            "error": str(e),
            "langflow_url": LANGFLOW_BASE_URL
        }

@app.post("/debug/test-flow")
async def debug_test_flow(flow_id: Optional[str] = None, api_key: Optional[str] = None):
    """Debug endpoint to test a specific flow"""
    try:
        test_message = "Hello, this is a test message"
        
        # Use provided flow_id or fallback to environment variable
        if not flow_id:
            flow_id = FLOW_ID
            
        if not flow_id:
            return {"error": "No flow ID provided and no FLOW_ID environment variable set"}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            
            # Test the flow
            langflow_payload = {
                "input_value": test_message,
                "output_type": "chat",
                "input_type": "chat",
                "tweaks": {}
            }
            
            langflow_url = f"{LANGFLOW_BASE_URL}/api/v1/run/{flow_id}"
            
            # Prepare headers with API key and content type
            run_headers = build_langflow_headers(api_key)
            run_headers["Content-Type"] = "application/json"
            
            response = await client.post(
                langflow_url,
                json=langflow_payload,
                headers=run_headers
            )
            
            result = {
                "flow_id": flow_id,
                "request_url": langflow_url,
                "request_payload": langflow_payload,
                "response_status": response.status_code,
                "response_headers": dict(response.headers),
                "response_text": response.text[:2000] + "..." if len(response.text) > 2000 else response.text
            }
            
            if response.status_code == 200 and response.text.strip():
                try:
                    result["response_json"] = response.json()
                except:
                    result["json_parse_error"] = "Could not parse response as JSON"
            
            return result
            
    except Exception as e:
        return {"error": str(e)}

# Mount static files directory
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
