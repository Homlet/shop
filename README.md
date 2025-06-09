# Home Assistant Add-on: Shopping List Organiser

[![License][license-shield]](LICENSE.md)

A Home Assistant addon that organizes shopping lists created with voice assistants. It processes the lists using LLM technology to deduplicate, categorize items by store sections, and format them for viewing on smartphones or printing on receipt paper.

## About

This Home Assistant add-on helps organize your shopping lists created with voice assistants. It connects to your Home Assistant todo lists, processes them using AI, and presents a neatly organized list sorted by store sections.

Key features:
- Direct integration with Home Assistant shopping lists
- Support for multiple todo list integrations (Alexa, Google Tasks, Todoist, etc.)
- AI-powered list processing (deduplication, categorization by store sections)
- Support for multiple store profiles with custom sections
- Formatting for receipt printers (58mm or 80mm)
- Mobile-responsive web interface
- Print and download functionality

## Installation

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https://github.com/Homlet/shop)

1. Click the button above or manually add the repository URL to your Home Assistant add-on store
2. Find the "Shopping List Organiser" add-on and click install
3. Configure the add-on (you'll need an LLM API key)
4. Start the add-on
5. Check the logs to make sure it started correctly

## License

MIT License
