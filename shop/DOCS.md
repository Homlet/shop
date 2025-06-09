# Shopping List Organiser

A Home Assistant addon that organizes shopping lists created with voice assistants. It processes the lists using LLM technology to deduplicate, categorize items by store sections, and format them for viewing on smartphones or printing on receipt paper.

## Installation

1. Add this repository to your Home Assistant instance:
   [![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/Homlet/shop)
2. Install the "Shopping List Organiser" add-on
3. Start the add-on
4. Check the logs to make sure it's working correctly

## Configuration

**Note**: You will need an OpenAI API key or an Anthropic API key to use this addon.

| Option | Description |
|--------|-------------|
| `llm_model` | LLM model ID (e.g., "gpt-3.5-turbo" or "anthropic/claude-3-sonnet-20240229") |
| `llm_api_key` | API key for the selected LLM provider |
| `todo_list_entity_id` | Entity ID of your shopping list in Home Assistant (e.g., "todo.shopping") |
| `default_store` | Default store name for categorization |
| `receipt_width` | Receipt paper width in characters (32 for 58mm printers, 48 for 80mm) |
| `log_level` | Logging level: DEBUG, INFO, WARNING, or ERROR |
| `stores` | List of store configurations with custom sections |

### Example Configuration

```yaml
llm_model: "gpt-3.5-turbo"
llm_api_key: "sk-yourapikey"
todo_list_entity_id: "todo.shopping"
default_store: "Grocery Store"
receipt_width: 32
log_level: "INFO"
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
```

## Usage

1. Add items to your Home Assistant shopping list (manually or via voice assistant)
2. Open the Shopping List Organiser web interface (from the sidebar or the addon info page)
3. Choose which store you're going to
4. Click "Process List"
5. View your organized list on screen or print it

## Supported Todo List Integrations

The addon supports any todo list that works with Home Assistant, including:

- Alexa Lists
- Google Tasks
- Todoist
- CalDAV
- Bring!
- Home Assistant's built-in shopping list

## Supported LLM Providers

The addon currently supports:

- OpenAI (GPT models)
- Anthropic (Claude models)

## Troubleshooting

If you encounter issues:

1. Check the addon logs for error messages
2. Verify your API key is correct
3. Make sure your todo list entity ID is correct
4. Check that you have items in your shopping list

## Support

For issues, feature requests, or questions, please [open an issue on GitHub](https://github.com/Homlet/shop/issues).