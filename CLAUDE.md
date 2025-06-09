# Shopping List Organiser - Claude Assistant Guidelines

## Project Overview
This is a Home Assistant addon that organizes shopping lists created with voice assistants. It processes lists using LLM technology to deduplicate items, categorize them by store sections, and format them for viewing on smartphones or printing on receipt paper.

## Key Technologies
- **Backend**: FastAPI, Python, Pydantic
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **Integrations**: Home Assistant Todo API, LLM APIs (OpenAI/Anthropic)
- **Deployment**: Docker container, Home Assistant addon

## Code Structure

### Core Components
- `app/main.py` - FastAPI application entry point
- `app/config.py` - Configuration management with Pydantic
- `app/services/` - Service modules:
  - `list_provider.py` - Integration with Home Assistant Todo lists
  - `llm_service.py` - LLM processing for shopping lists
  - `formatter.py` - Formats processed lists for display/printing
- `app/static/` - Frontend assets (HTML, CSS, JS)

### Configuration
- `config.yaml` - Home Assistant addon configuration
- `.env` - Local development environment variables

## Development Guidelines

### Configuration Management
- Always maintain both `.env` and `config.yaml` in sync
- Use Pydantic for type validation and environment variable loading
- The `Settings` class in `config.py` is the source of truth for all configuration

### Home Assistant Integration
- Direct integration with Home Assistant Todo API
- Support for multiple list integrations (Alexa, Google Tasks, Todoist, etc.)
- Robust fallback mechanisms for different integration types

### LLM Integration
- Support for multiple LLM providers (OpenAI and Anthropic)
- Use structured prompting for consistent results
- Store sections are dynamically populated from configuration

### Store Configuration
- Stores are configured with custom sections in `config.yaml`
- Each store has a name and a list of sections for organization
- LLM prompts are dynamically generated with store-specific sections

### Code Conventions
- Use async/await for all I/O operations
- Factory functions for service instantiation
- Comprehensive error handling with proper logging
- Service-oriented architecture with clear responsibilities

## Common Tasks

### Adding a New Feature
1. Update `moscow.md` if needed
2. Implement the feature in the appropriate service
3. Update `PROGRESS.md` to track completion
4. Ensure configuration consistency between `.env` and `config.yaml`

### Testing
- Manual testing with FastAPI's auto-reload feature
- Test with different Home Assistant todo list integrations

### Environment Variables Format
- For simple values, use standard KEY=VALUE format
- For complex structures (like the store configuration), use single-line JSON strings

## Important Considerations
- Focus on simplicity and reliability
- Maintain compatibility with various Home Assistant todo list integrations
- Ensure responsive design for mobile devices
- Format lists properly for thermal receipt printers (32 or 48 character width)