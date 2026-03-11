import base64
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


CANONICAL_MEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": {"type": "string"},
                },
                "required": ["name", "quantity", "unit"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["summary", "items", "notes"],
    "additionalProperties": False,
}


async def canonicalize_from_text(text: str) -> dict:
    """
    Convert a raw text meal description into a canonical meal object.

    Returns a dict like:
    {
        "summary": "2 tuna sandwiches and 1 banana",
        "items": [
            {
                "name": "tuna sandwich",
                "quantity": 2,
                "unit": "pieces"
            },
            {
                "name": "banana",
                "quantity": 1,
                "unit": "piece"
            }
        ],
        "notes": ""
    }
    """

    logger.info("Canonical text parsing called")
    logger.info("Text: %s", text)

    prompt = f"""
Convert the following meal description into a canonical meal object.

Meal description:
{text}

Return:
- summary: short description of the whole meal
- items: structured list of food items
- notes: short optional notes

Rules:
- Preserve explicit quantities when given.
- If quantity is implied, choose a realistic default.
- Normalize repeated identical items into quantities when appropriate.
- The summary must describe the whole meal.
- Do not estimate calories or protein.
- Be realistic and concise.

Good example:
{{
  "summary": "2 tuna sandwiches and 1 banana",
  "items": [
    {{
      "name": "tuna sandwich",
      "quantity": 2,
      "unit": "pieces"
    }},
    {{
      "name": "banana",
      "quantity": 1,
      "unit": "piece"
    }}
  ],
  "notes": ""
}}
""".strip()

    try:
        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meal_description",
                    "schema": CANONICAL_MEAL_SCHEMA,
                    "strict": True,
                }
            },
        )
    except Exception:
        logger.exception("OpenAI text canonicalization failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse canonical text response as JSON")
        raise

    logger.info("Canonical text meal: %s", data)
    return data


async def canonicalize_from_image(image_path: str, caption: str | None = None) -> dict:
    """
    Convert a meal photo into a canonical meal object.

    Returns a dict like:
    {
        "summary": "2 tuna salad toasts",
        "items": [
            {
                "name": "tuna salad toast",
                "quantity": 2,
                "unit": "pieces"
            }
        ],
        "notes": "open-faced, toasted bread"
    }
    """

    logger.info("Canonical image parsing called")
    logger.info("Image path: %s", image_path)
    logger.info("Caption: %s", caption)

    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        logger.exception("Failed to read image file: %s", image_path)
        raise

    caption_text = caption or "No caption provided"

    prompt = f"""
Analyze the meal photo and return a canonical meal object.

Additional details from the user: {caption_text}

Return:
- summary: short description of the whole meal
- items: structured list of visible food items
- notes: short optional notes

Rules:
- Describe all visible food in the image.
- If multiple identical items are visible, include the correct quantity.
- The summary must describe the whole meal, not just one item.
- Do not estimate calories or protein.
- Be realistic and concise.
- If an exact ingredient is uncertain, use the most likely plain description.

Good example:
{{
  "summary": "2 tuna salad toasts",
  "items": [
    {{
      "name": "tuna salad toast",
      "quantity": 2,
      "unit": "pieces"
    }}
  ],
  "notes": "open-faced, toasted bread"
}}
""".strip()

    try:
        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{image_b64}",
                            "detail": "low",
                        },
                    ],
                }
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meal_description",
                    "schema": CANONICAL_MEAL_SCHEMA,
                    "strict": True,
                }
            },
        )
    except Exception:
        logger.exception("OpenAI image canonicalization failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse canonical image response as JSON")
        raise

    logger.info("Canonical image meal: %s", data)
    return data