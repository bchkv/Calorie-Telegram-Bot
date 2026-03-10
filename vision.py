import base64
import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def estimate_meal(image_path: str, description: str | None = None) -> dict:
    """
    Estimate calories and protein from a meal photo using structured JSON output.
    Returns a dict like:
    {
        "dish": "2 tuna salad toasts",
        "calories": 420,
        "protein": 28
    }
    """

    logger.info("Vision module called")
    logger.info("Image path: %s", image_path)
    logger.info("Description: %s", description)

    try:
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        logger.exception("Failed to read image file: %s", image_path)
        raise

    caption_text = description or "No description provided"

    prompt = f"""
Estimate calories and protein of all the food in the photo.

Additional details about the meal: {caption_text}

Return:
- short dish name
- total calories in kcal
- total protein in grams

Rules:
- Nutrition values must cover all visible food in the image.
- The dish field must describe the whole plate/meal, not just one piece.
- If multiple identical pieces are visible, include that quantity in the dish name itself.
- Use compound dish names when appropriate.

Good examples of dish names:
- "2 tuna salad toasts"
- "2 open-faced tuna sandwiches"
- "3 chicken tacos"
- "2 slices of pizza"

Bad examples:
- "sandwich" if two sandwiches are visible
- "toast" if two toasts are visible

Be realistic and concise.
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
                    "name": "meal_estimate",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dish": {"type": "string"},
                            "calories": {"type": "number"},
                            "protein": {"type": "number"},
                        },
                        "required": ["dish", "calories", "protein"],
                        "additionalProperties": False,
                    },
                    "strict": True,
                }
            },
        )
    except Exception:
        logger.exception("OpenAI vision request failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse vision response as JSON")
        raise

    logger.info("Structured output: %s", data)
    return data

async def estimate_text_meal(description: str) -> dict:
    logger.info("Text estimation: %s", description)

    try:
        response = await client.responses.create(
            model="gpt-4.1-mini",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meal_estimate",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "dish": {"type": "string"},
                            "calories": {"type": "number"},
                            "protein": {"type": "number"}
                        },
                        "required": ["dish", "calories", "protein"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            input=f"""
Estimate calories and protein for the following meal.

Meal description:
{description}

Return realistic approximate values.
"""
        )
    except Exception:
        logger.exception("OpenAI text meal request failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse text meal response as JSON")
        raise

    logger.info("Structured output: %s", data)

    return data