import os
import requests
import json
from dotenv import load_dotenv
import aiohttp

load_dotenv()

async def llm_call(text):
    """
    Calls the Gemini API to generate content based on the provided text.

    Args:
        text (str): The input text to be processed by the Gemini API.

    Returns:
        str: The generated content from the Gemini API.

    Raises:
        KeyError: If the response does not contain the expected keys.
        requests.exceptions.RequestException: If there is an issue with the HTTP request.

    Environment Variables:
        GEMINI_API_KEY: The API key for authenticating with the Gemini API.
    """
    print("Calling LLM...")
    api_key = os.getenv('GEMINI_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": text
                    }
                ]
            }
        ]
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response_data = await response.json()
            return response_data['candidates'][0]['content']['parts'][0]['text']

# Example usage
if __name__ == "__main__":
    import asyncio

    result = asyncio.run(llm_call("Explain how AI works"))
    print(result)