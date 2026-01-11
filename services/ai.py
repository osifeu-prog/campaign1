from openai import OpenAI
from config.settings import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def analyze_expert_request(text: str) -> str:
    if not _client:
        return "AI analysis disabled"

    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "נתח בקשת מועמד כמומחה וסווג תחום מקצועי בקצרה.",
            },
            {"role": "user", "content": text},
        ],
    )

    return response.choices[0].message.content.strip()
