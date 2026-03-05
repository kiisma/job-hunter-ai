"""
Product scraper using Claude Agent SDK with built-in WebFetch.

The agent autonomously visits the product URL, reads the page,
and returns structured JSON — no Playwright or Chromium required.
"""
import json
import logging
import re

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

from .config import ANTHROPIC_API_KEY
from .models import ProductInfo

logger = logging.getLogger(__name__)

_PROMPT = """Visit this product page and extract information for a shipping cost calculator.

URL: {url}

After reading the page return ONLY a valid JSON object — no other text, no markdown fences:
{{
  "name": "<full product name including brand, model, colour/size if visible>",
  "price": <numeric price in EUR as float — convert from other currencies if needed>,
  "currency": "EUR",
  "weight_kg": <estimated weight in kg as float based on product type>,
  "shipping_to_portugal": <shipping cost to Portugal in EUR as float, 0.0 if free or not shown>
}}

Weight estimation guide:
- T-shirt / top: 0.3 kg  |  Jeans / trousers: 0.7 kg  |  Dress / skirt: 0.5 kg
- Jacket / coat: 1.2 kg  |  Shoes / boots: 1.2 kg      |  Sneakers: 0.8 kg
- Handbag: 0.6 kg        |  Smartphone: 0.2 kg          |  Laptop: 2.0 kg
- Tablet: 0.5 kg         |  Book: 0.4 kg                |  Perfume (50ml): 0.2 kg
- Unknown / other: 0.5 kg

Rules:
- Convert all prices to EUR.
- If Portugal shipping is free or not mentioned → 0.0.
- Return ONLY the raw JSON object."""


def _parse_json(text: str) -> dict:
    text = text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    # Find the first {...} block (agent might add a sentence before/after)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


async def scrape_product(url: str) -> ProductInfo:
    """Return ProductInfo for the given URL using Claude Agent SDK + WebFetch."""
    result_text = ""

    async for message in query(
        prompt=_PROMPT.format(url=url),
        options=ClaudeAgentOptions(
            allowed_tools=["WebFetch"],
            model="claude-opus-4-6",
            max_turns=5,
            # Pass the API key to the agent subprocess explicitly
            env={"ANTHROPIC_API_KEY": ANTHROPIC_API_KEY},
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    if not result_text:
        raise RuntimeError(f"Agent returned no result for {url}")

    data = _parse_json(result_text)

    return ProductInfo(
        url=url,
        name=data.get("name") or "Unknown product",
        price=float(data.get("price") or 0.0),
        currency=data.get("currency") or "EUR",
        weight_kg=float(data.get("weight_kg") or 0.5),
        shipping_to_portugal=float(data.get("shipping_to_portugal") or 0.0),
    )
