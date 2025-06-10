import logging
import os
from typing import Dict, List, Optional, Any
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Query,
    BackgroundTasks,
    Request,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .services.list_provider import (
    get_list_provider,
    HomeAssistantListProvider,
)
from .services.llm_service import get_llm_service, LLMService
from .services.formatter import get_formatter, ReceiptFormatter

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Shopping List Organiser",
    description="Voice-to-print shopping list processor",
    version="0.0.1",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/static")

# Service instances
list_provider = get_list_provider()
llm_service = get_llm_service()
formatter = get_formatter()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await list_provider.close()
    await llm_service.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main index page with ingress path handling."""
    # Read the index.html file
    with open("app/static/index.html", "r") as f:
        content = f.read()

    # Check if running in Home Assistant ingress mode
    ingress_path = request.headers.get("X-Ingress-Path", "")
    if ingress_path:
        # Inject the ingress base path as a variable for the frontend
        script_tag = (
            f'<script>window.ingressBasePath = "{ingress_path}";</script>'
        )
        # Insert the script right before the closing </head> tag
        content = content.replace("</head>", f"{script_tag}</head>")
        logger.info(f"Serving with ingress path: {ingress_path}")

    return HTMLResponse(content=content)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/items")
async def get_items(
    limit: Optional[int] = Query(
        5, description="Maximum number of items to return"
    ),
):
    """Get items from the configured shopping list with optional limit."""
    try:
        result = await list_provider.get_list_items(limit=limit)
        return result
    except Exception as e:
        logger.exception("Error fetching list items")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process")
@app.get("/api/process")
async def process_list(
    store_name: Optional[str] = Query(
        None, description="Store name for context"
    ),
    format_type: str = Query(
        "text", description="Output format: text or html"
    ),
    limit: Optional[int] = Query(
        None, description="Optional limit for items to process"
    ),
):
    """Process the shopping list through the LLM and format it for output."""
    try:
        # Get list items
        result = await list_provider.get_list_items(limit=limit)
        items = result["items"]

        if not items:
            raise HTTPException(
                status_code=404, detail="List is empty or not found"
            )

        # Process with LLM
        processed_text = await llm_service.process_shopping_list(
            items, store_name
        )

        # Format for output
        if format_type.lower() == "html":
            formatted_output = formatter.format_for_html(
                processed_text, store_name
            )
            return {"format": "html", "content": formatted_output}
        else:
            formatted_output = formatter.format_for_receipt(
                processed_text, store_name
            )
            return {"format": "text", "content": formatted_output}

    except Exception as e:
        logger.exception("Error processing list")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stores")
async def get_stores():
    """Get available store profiles from configuration."""
    # Convert the stores from the config to the format expected by the frontend
    stores = []
    for store in settings.stores:
        store_id = store["name"].lower().replace(" ", "_")
        stores.append(
            {
                "id": store_id,
                "name": store["name"],
                "sections": store["sections"],
            }
        )

    return {"stores": stores}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host=settings.host, port=settings.port, reload=True
    )
