# Shopping List Organizer

A Home Assistant addon that organizes shopping lists created with voice assistants (Alexa + AnyList). It processes the lists using LLM technology to deduplicate, categorize items by store sections, and format them for viewing on smartphones or printing on receipt paper.

## Features

- Integration with AnyList API to fetch shopping lists created with Alexa
- LLM processing for list deduplication and store section categorization
- Formatting for receipt printers (58mm thermal printer compatible)
- Mobile-responsive web interface for viewing processed lists
- Print functionality for thermal printers
- Store selection for better categorization context
- Download as text file

## Setup and Installation

### Prerequisites

- Home Assistant instance
- Alexa with AnyList skill enabled
- AnyList account credentials
- OpenAI API key or Anthropic Claude API key

### Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Shopping List Organizer" add-on
3. Configure the add-on with your credentials:
   - AnyList email and password
   - LLM provider choice (OpenAI or Anthropic)
   - LLM API key
   - Default store name

### Configuration Options

| Option | Description |
|--------|-------------|
| `anylist_email` | Your AnyList account email |
| `anylist_password` | Your AnyList account password |
| `llm_provider` | LLM provider to use: "openai" or "anthropic" |
| `llm_api_key` | API key for the selected LLM provider |
| `default_store` | Default store name for categorization |
| `receipt_width` | Receipt paper width in characters (32 for 58mm printers, 48 for 80mm) |
| `log_level` | Logging level: DEBUG, INFO, WARNING, or ERROR |

## Usage

1. Create a shopping list using Alexa + AnyList
2. Open the Shopping List Organizer web interface
3. Select your shopping list
4. Choose which store you're going to
5. Click "Process List"
6. View your organized list on screen or print it

## Development

### Local Development Setup

1. Clone this repository
2. Create a `.env` file with the required environment variables (see below)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m uvicorn app.main:app --reload`

### Environment Variables

```
ANYLIST_EMAIL=your-email@example.com
ANYLIST_PASSWORD=your-password
LLM_PROVIDER=openai
LLM_API_KEY=your-api-key
DEFAULT_STORE=Grocery Store
RECEIPT_WIDTH=32
LOG_LEVEL=INFO
```

### Building the Docker Image

```bash
docker build -t shopping-list-organizer .
docker run -p 8080:8080 shopping-list-organizer
```
