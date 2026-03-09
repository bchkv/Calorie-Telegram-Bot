import base64
import json

from dotenv import load_dotenv
import os
from openai import AsyncOpenAI

import logging

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def estimate_meal(image_path: str, description: str | None = None) -> dict:
    """
    Estimate calories and protein from a meal photo using structured JSON output.
    Returns a dict like:
    {
        "dish": "...",
        "calories": 123,
        "protein": 12
    }
    """

    logger.info("Vision module called")
    logger.info("Image path: %s", image_path)
    logger.info("Description: %s", description)

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    caption_text = description or "No description provided"

    response = await client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"""
Estimate the meal in this image.

User description: {caption_text}

Estimate:
- dish name
- total calories in kcal
- total protein in grams

Return realistic approximate values for the whole visible meal.
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{image_b64}",
                        "detail": "low"
                    }
                ]
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
                        "protein": {"type": "number"}
                    },
                    "required": ["dish", "calories", "protein"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    )


    data = json.loads(response.output_text)

    logger.info("Structured output: %s", data)

    return data


async def estimate_text_meal(description: str) -> dict:
    logger.info("Text estimation: %s", description)

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
                }
            }
        },
        input=f"""
Estimate calories and protein for the following meal.

Meal description:
{description}

Return realistic approximate values.
"""
    )

    data = json.loads(response.output[0].content[0].text)

    logger.info("Structured output: %s", data)

    return data
