import base64
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def describe_meal_from_image(image_path: str, caption: str | None = None) -> dict:
    """
    Extract a canonical meal description from a meal photo.

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
        "notes": "open-faced, toasted white bread"
    }
    """

    logger.info("Vision description called")
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
Analyze the meal photo and return a canonical meal description.

Additional details from the user: {caption_text}

Return:
- summary: short description of the whole meal
- items: structured list of visible food items
- notes: short optional notes

Rules:
- Describe all visible food in the image.
- If multiple identical items are visible, include the correct quantity.
- The summary must describe the whole meal, not just one item.
- Be realistic and concise.
- Do not estimate calories or protein.
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
                    "schema": {
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
                    },
                    "strict": True,
                }
            },
        )
    except Exception:
        logger.exception("OpenAI vision description request failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse vision description response as JSON")
        raise

    logger.info("Canonical meal description: %s", data)
    return data