# Technical Implementation Plan: Shopping List Organizer HA Addon

## Tech Stack

**Backend Framework:** FastAPI (Python)
- Lightweight, async-capable, perfect for API integrations
- Excellent OpenAPI documentation generation
- ARM64 compatible

**Frontend:** HTML/CSS/JavaScript (Vanilla or lightweight framework)
- Keep it simple for HA addon context
- Bootstrap or Tailwind for responsive design
- Fetch API for backend communication

**LLM Integration:** OpenAI API or Anthropic Claude API
- HTTP client library (httpx for async Python)
- Structured prompting for consistent categorization

**List Service Integration:** 
- Home Assistant Todo API integration
- Specialized handlers for different todo list integrations (especially Bring!)
- HTTP client with proper authentication handling

**Containerization:** Docker
- Multi-stage build for smaller image size
- ARM64 base image (python:3.11-slim-bullseye)

**Configuration:** YAML + Environment Variables
- HA addon config.yaml for user settings
- Python-dotenv for environment management

## Project Structure
```
shop/
├── Dockerfile
├── config.yaml              # HA addon config
├── run.sh                   # Startup script
├── requirements.txt
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings management
│   ├── services/
│   │   ├── list_provider.py # Home Assistant Todo API integration
│   │   ├── llm_service.py   # OpenAI/Claude integration
│   │   └── formatter.py     # Receipt formatting
│   └── static/              # Frontend files
└── README.md
```

## MVP Development Roadmap

### Phase 1: Core Pipeline (Week 1-2)
**Goal:** Get basic list → LLM → formatted output working
1. Set up FastAPI skeleton with health check endpoint
2. Implement Home Assistant Todo API integration (fetch lists)
3. Add specialized support for different todo list integrations (Bring!, etc.)
4. Create basic LLM service with structured prompting
5. Build simple receipt formatter (plain text first)
6. Create minimal web UI with "Process List" button

### Phase 2: HA Integration (Week 3)
**Goal:** Make it work as HA addon
1. Create Dockerfile with ARM64 compatibility
2. Write HA addon configuration files
3. Implement addon options integration
4. Test on Raspberry Pi 4 environment
5. Add basic error handling and logging

### Phase 3: User Experience (Week 4)
**Goal:** Make it actually usable
1. Improve web UI responsiveness
2. Add processing status indicators
3. Implement print functionality (if printer available)
4. Add basic configuration management
5. Error handling for API failures

### Phase 4: Polish (Week 5)
**Goal:** Production ready
1. Add export functionality (PDF/text)
2. Implement store selection for LLM context
3. Receipt formatting improvements
4. Documentation and installation guide
5. Testing and bug fixes

## Key Implementation Notes

**LLM Prompting Strategy:**
```python
prompt = f"""
Process this shopping list for {store_name}:
{raw_list}

Tasks:
1. Remove duplicates (combine quantities)
2. Sort into store sections: {sections_text}
3. Format for 58mm receipt paper (max 32 chars width)

Output as structured text ready for printing.
"""
```

**HA Addon Config Template:**
```yaml
name: Shopping List Organizer
version: "1.0.0"
slug: shopping_list_organizer
description: Voice-to-print shopping list processor
arch:
  - aarch64
ports:
  8080/tcp: 8080
options:
  ha_url: "http://supervisor/core"  # Default for HA addons
  ha_token: ""  # Long-lived access token
  todo_list_entity_id: "todo.shopping"  # Entity ID of your shopping list in Home Assistant
  llm_model: ""  # Required: model ID like gpt-3.5-turbo or anthropic/claude-3-sonnet-20240229
  llm_api_key: ""  # Required: API key for the selected model provider
  default_store: "Grocery Store"
  stores:
    - name: "Grocery Store"
      sections:
        - "Produce"
        - "Dairy"
        - "Meat"
        - "Pantry"
        - "Frozen"
        - "Household"
    - name: "Supermarket"
      sections:
        - "Fruits & Vegetables"
        - "Dairy & Eggs"
        - "Meat & Seafood" 
        - "Bakery"
        - "Canned Goods"
        - "Frozen Foods"
        - "Cleaning Supplies"
    - name: "Convenience Store"
      sections:
        - "Snacks"
        - "Beverages"
        - "Quick Meals"
        - "Essentials"
```

**Docker Optimization:**
- Use multi-stage build to minimize image size
- Install only production dependencies
- Use ARM64 base images throughout

This plan prioritizes getting the core functionality working quickly, then layering on the HA integration and user experience improvements. The tech stack is intentionally simple and proven for ARM64/Raspberry Pi environments.
