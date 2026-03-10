import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def parse_meal_from_text(text: str) -> dict:
    logger.info("Text meal parsing: %s", text)

    prompt = f"""
Convert the following meal description into a canonical meal object.

Meal description:
{text}

Return:
- summary
- items
- notes

Rules:
- Preserve explicit quantities when given.
- If quantity is implied, choose a realistic default.
- Do not estimate calories or protein.
- Be realistic and concise.
""".strip()

    try:
        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
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
        logger.exception("OpenAI text meal parsing failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse text meal response as JSON")
        raise

    logger.info("Canonical text meal: %s", data)
    return data