"""
Battle Card Generator - Flask web app
Generates AI-powered competitor battle cards using the Google Gemini API.

Pipeline (mirrors the reference notebook, battle-card-generator.ipynb):
    1. User submits competitor + product info via the web form
    2. mcp_web_search() researches the competitor
    3. generate_battle_card() sends the research + user inputs to Gemini
    4. The result is rendered as a formatted battle card
"""

import os
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, render_template, request
from google import genai

# ============================================================
# SETUP & SECURITY
# API key is loaded from .env — never hardcoded.
# This follows the security pillar of agentic engineering:
# zero ambient authority, least-privilege credential access.
# ============================================================
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY not found. Copy .env.example to .env and add your key."
    )

client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

app = Flask(__name__)


# ============================================================
# MCP WEB SEARCH TOOL
# Modular tool following the MCP pattern: Discover > Configure > Connect
# The agent calls this tool to research any competitor by name.
# Kept separate from the agent logic for reusability.
# ============================================================
def mcp_web_search(competitor_name):
    """
    MCP-style tool: researches a competitor by name.
    Discovers their web presence and returns cleaned content
    for the agent to analyze.
    """
    search_url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote(competitor_name + " product features pricing")
    )
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract competitor's actual website from search results
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/url?q=" in href:
            actual_url = href.split("/url?q=")[1].split("&")[0]
            if competitor_name.lower().replace(" ", "") in actual_url.lower():
                links.append(actual_url)

    if links:
        # Scrape the competitor's page
        try:
            page = requests.get(links[0], headers=headers, timeout=10)
            page_soup = BeautifulSoup(page.text, "html.parser")
            for tag in page_soup(["nav", "footer", "script", "style"]):
                tag.decompose()
            return page_soup.get_text(separator=" ", strip=True)[:3000]
        except requests.RequestException:
            pass

    # Fallback: use Google search text directly
    for tag in soup(["nav", "footer", "script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)[:3000]


# ============================================================
# BATTLE CARD AGENT
# Orchestrates the full pipeline:
# 1. Calls the MCP tool to research the competitor
# 2. Passes the research to Gemini with a structured prompt
# 3. Returns a formatted, ready-to-use battle card
# Agent design follows the single-responsibility principle —
# one agent, one job, modular tools.
# ============================================================
def generate_battle_card(competitor_name, your_product_name, your_key_strengths):
    """
    Main agent pipeline:
    Step 1 — MCP tool researches the competitor
    Step 2 — Gemini agent analyzes and generates the battle card
    """
    # Step 1: MCP tool call
    competitor_info = mcp_web_search(competitor_name)

    # Step 2: Gemini agent generates the battle card
    prompt = f"""
    You are an expert sales enablement agent. Analyze this competitor information
    and generate a professional sales battle card.

    COMPETITOR: {competitor_name}
    COMPETITOR RESEARCH: {competitor_info}

    OUR PRODUCT: {your_product_name}
    OUR KEY STRENGTHS: {your_key_strengths}

    Generate a battle card with these exact sections:

    ## 🏢 Competitor Overview
    (2-3 sentence summary of who they are)

    ## 💪 Their Strengths
    (3-4 bullet points)

    ## ⚠️ Their Weaknesses
    (3-4 bullet points)

    ## 🏆 Our Winning Differentiators
    (3-4 bullet points of why we win)

    ## 🗣️ Common Objections & Responses
    (3 objections they raise + our killer responses)

    ## ⚡ Quick Pitch When You Meet Them
    (2-3 sentence elevator pitch to use in the field)
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text


# ============================================================
# MARKDOWN -> HTML FORMATTING
# Gemini returns the battle card as markdown (same as the notebook,
# which rendered it with IPython's Markdown display). The web app
# has no notebook renderer, so this converts the markdown headings,
# bullet lists, and bold text into HTML for the results page.
# ============================================================
def markdown_to_html(text):
    """Lightweight markdown-to-HTML conversion for battle card output."""
    html_lines = []
    in_list = False

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)

        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith(("- ", "* ")):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:].strip()}</li>")
        elif line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


# ============================================================
# ROUTES
# ============================================================
@app.route("/", methods=["GET"])
def index():
    """Render the input form."""
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    """Handle form submission and render the generated battle card."""
    competitor_name = request.form.get("competitor_name", "").strip()
    your_product_name = request.form.get("your_product_name", "").strip()
    your_key_strengths = request.form.get("your_key_strengths", "").strip()

    if not competitor_name or not your_product_name or not your_key_strengths:
        return render_template(
            "index.html",
            error="Please fill in all fields before generating a battle card.",
        )

    try:
        battle_card_text = generate_battle_card(
            competitor_name, your_product_name, your_key_strengths
        )
        battle_card_html = markdown_to_html(battle_card_text)
    except Exception as exc:  # user-friendly error surface for API/network failures
        return render_template(
            "index.html",
            error=f"Something went wrong generating the battle card: {exc}",
        )

    return render_template(
        "result.html",
        competitor_name=competitor_name,
        battle_card_html=battle_card_html,
    )


if __name__ == "__main__":
    app.run(debug=True)
