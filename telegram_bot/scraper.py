"""
Product scraper using Playwright (headless Chromium) for page rendering
and Claude claude-opus-4-6 for intelligent data extraction.
"""
import json
import logging
import re

import anthropic
from playwright.async_api import async_playwright

from .config import ANTHROPIC_API_KEY
from .models import ProductInfo

logger = logging.getLogger(__name__)

_CLAUDE_SYSTEM = (
    "You are a product information extractor for an e-commerce shipping calculator. "
    "Extract data accurately and estimate weights based on your knowledge of product categories."
)

_EXTRACTION_PROMPT = """Extract product information from the following e-commerce page and return ONLY a valid JSON object.

URL: {url}

PAGE TEXT (extracted, may be truncated):
{text}

Return this exact JSON structure:
{{
  "name": "<full product name including brand, model, color/size if visible>",
  "price": <numeric price as float, 0.0 if not found>,
  "currency": "<3-letter ISO code, e.g. EUR, USD, GBP — default EUR>",
  "weight_kg": <estimated weight in kg as float based on product type>,
  "shipping_to_portugal": <shipping cost to Portugal in EUR as float, 0.0 if free or not shown>
}}

Weight estimation guide (use your knowledge):
- T-shirt / light top: 0.3 kg
- Jeans / trousers: 0.7 kg
- Dress / skirt: 0.5 kg
- Jacket / coat: 1.2 kg
- Shoes / boots: 1.0–1.5 kg
- Sneakers: 0.8 kg
- Handbag / purse: 0.6 kg
- Smartphone: 0.2 kg
- Laptop: 2.0 kg
- Tablet: 0.5 kg
- Book: 0.4 kg
- Perfume (50 ml): 0.2 kg
- Cosmetics / small items: 0.3 kg
- Unknown: 0.5 kg

Rules:
- If price is NOT in EUR, convert to EUR using approximate current rates.
- If shipping to Portugal is explicitly FREE, use 0.0.
- If shipping cost is shown for Portugal/PT, extract that value in EUR.
- If no shipping info is visible, use 0.0.
- Return ONLY the JSON — no markdown, no explanation.
"""


async def _fetch_page_text(url: str) -> str:
    """Fetch a page using Playwright and return its visible text content."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="pt-PT",
            extra_http_headers={"Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8"},
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            # Give JS-rendered content a moment to settle
            await page.wait_for_timeout(2_500)
            # Extract visible text (much cheaper than full HTML for Claude)
            text = await page.evaluate(
                """() => {
                    // Remove script/style noise
                    const remove = document.querySelectorAll('script, style, noscript, svg');
                    remove.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }"""
            )
        finally:
            await browser.close()
    # Trim to ~12 000 chars to stay well within token limits
    return text[:12_000]


def _clean_json(raw: str) -> str:
    """Strip markdown fences if Claude wrapped the JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()


async def scrape_product(url: str) -> ProductInfo:
    """Return a ProductInfo for the given URL using Playwright + Claude."""
    page_text = await _fetch_page_text(url)

    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    prompt = _EXTRACTION_PROMPT.format(url=url, text=page_text)

    # Use streaming to avoid timeout on slow responses
    async with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=512,
        thinking={"type": "adaptive"},
        system=_CLAUDE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        response = await stream.get_final_message()

    # Find the text block (adaptive thinking may return a thinking block first)
    raw_text = next(
        (block.text for block in response.content if block.type == "text"),
        "{}",
    )

    data = json.loads(_clean_json(raw_text))

    return ProductInfo(
        url=url,
        name=data.get("name") or "Unknown product",
        price=float(data.get("price") or 0.0),
        currency=data.get("currency") or "EUR",
        weight_kg=float(data.get("weight_kg") or 0.5),
        shipping_to_portugal=float(data.get("shipping_to_portugal") or 0.0),
    )
