import requests
from config import AI_API_KEY, AI_API_URL, AI_MODEL


def ask_ai(messages):
    if not AI_API_KEY:
        return "AI_API_KEY is not configured."

    if not AI_API_URL:
        return "AI_API_URL is not configured."

    if not AI_MODEL:
        return "AI_MODEL is not configured."

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": AI_MODEL,
        "messages": messages,
    }

    response = requests.post(
        AI_API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]
