import json
import logging
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

load_dotenv(override=True)
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def estimate_nutrition_from_canonical(meal: dict) -> dict:
    """
    Estimate calories and protein from a canonical meal object.

    Expected input example:
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

    Returns:
    {
        "dish": "2 tuna salad toasts",
        "calories": 420,
        "protein": 28
    }
    """

    logger.info("Nutrition estimation called with meal: %s", meal)

    prompt = f"""
Estimate calories and protein from this canonical meal description.

Meal:
{json.dumps(meal, ensure_ascii=False, indent=2)}

Return:
- dish: short description of the whole meal
- calories: total kcal for all items combined
- protein: total grams of protein for all items combined

Rules:
- Use the quantities in the items list.
- Return totals for the whole meal, not per-item values.
- If quantity is 2 or more, calories and protein must reflect the full combined amount.
- The dish field should describe the whole meal concisely.
- Be realistic and concise.

Good example:
If the meal has 2 tuna salad toasts, return totals for both toasts together.

Bad example:
dish = "2 tuna salad toasts"
calories = value for 1 toast
protein = value for 1 toast
""".strip()

    try:
        response = await client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
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
        logger.exception("OpenAI nutrition estimation request failed")
        raise

    try:
        data = json.loads(response.output_text)
    except Exception:
        logger.exception("Failed to parse nutrition response as JSON")
        raise

    logger.info("Nutrition estimate: %s", data)
    return data