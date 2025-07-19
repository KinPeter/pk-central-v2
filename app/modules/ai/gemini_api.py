import json
from logging import Logger
import re
from google import genai
from google.genai import Client
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
)


class GeminiApi:
    """
    A class to interact with the Gemini API.
    """

    def __init__(self, api_key: str, logger: Logger):
        self.client: Client = genai.Client(api_key=api_key)
        self.logger: Logger = logger

    async def generate_json(
        self, prompt: str, model: str = "gemini-2.0-flash-001"
    ) -> dict:
        """
        Generate text in JSON format using the Gemini API.
        """
        response = await self.client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=GenerateContentConfig(
                tools=[Tool(google_search=GoogleSearch())],
            ),
        )
        if not response.text:
            self.logger.error(
                "No response text received from the Gemini API.", str(response)
            )
            raise ValueError("No response text received from the Gemini API.")

        return self.extract_json(response.text)

    def extract_json(self, text: str) -> dict:
        """
        Extract JSON from the text response.
        NOTE: Won't work if the JSON contains nested objects!
        """
        match = re.search(r"\{.*?\}", text, re.DOTALL)
        if not match:
            self.logger.error("No valid JSON found in the response:", text)
            raise ValueError("No valid JSON found in the response.")

        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error("Invalid JSON format:", str(e))
            raise ValueError(f"Invalid JSON format: {e}")
