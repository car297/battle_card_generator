# AGENTS.md — Battle Card Generator

## Project Overview
This is a Python Flask web app called Battle Card Generator. It is a sales 
enablement tool that generates professional competitor battle cards using 
the Google Gemini API.

## Reference Implementation
The working implementation is in `Battle Card Generator.ipynb`. Use this 
notebook as the source of truth for:
- The exact Gemini API client setup (google-genai SDK, not google-generativeai)
- The mcp_web_search() function implementation
- The generate_battle_card() function and prompt structure
- The model name: gemini-3.5-flash-lite

## What To Build
A Flask web app with:
1. A clean input form (index.html) with three fields:
   - Competitor Name (text input)
   - Your Product Name (text input)
   - Your Key Strengths (textarea)
2. A results page (result.html) that displays the formatted battle card
3. app.py — the Flask backend that calls the Gemini API
4. requirements.txt — all dependencies
5. .env.example — placeholder for GOOGLE_API_KEY (never hardcode keys)

## Architecture
Follow the exact same pipeline as the notebook:
- User submits the form
- mcp_web_search() researches the competitor
- generate_battle_card() calls Gemini with the research + user inputs
- Result is displayed as formatted HTML

## Security Rules
- NEVER hardcode API keys
- Load GOOGLE_API_KEY from .env using python-dotenv
- Add .env to .gitignore

## Code Style
- Keep functions modular and single-responsibility
- Add comments explaining each major step
- Handle errors gracefully with user-friendly messages
- Follow the same comment style as the notebook

## Dependencies
- flask
- google-genai
- requests
- beautifulsoup4
- python-dotenv
