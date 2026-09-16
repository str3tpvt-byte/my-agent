import os
import requests

MODEL = "gemini-3.5-flash-lite"

API_URL = (
    f"https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
)


def ask_ai(prompt):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return "ERROR: GEMINI_API_KEY is not set."

    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=60,
        )

    except requests.exceptions.Timeout:
        return "ERROR: Gemini request timed out."

    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to Gemini. Check your Internet/DNS connection."

    except requests.exceptions.RequestException as error:
        return f"ERROR: Gemini network request failed: {error}"

    if response.status_code != 200:
        return (
            f"Gemini API error {response.status_code}: "
            f"{response.text[:500]}"
        )

    try:
        data = response.json()

        return data["candidates"][0]["content"]["parts"][0]["text"]

    except (KeyError, IndexError, TypeError, ValueError):
        return f"ERROR: Unexpected Gemini response: {data}"
