from openai import OpenAI
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

class LLMClient:
    def __init__(self, model_name: str, temperature: float = 0.0):
        self.model = model_name
        if model_name.startswith("gpt"):
            self.temperature = temperature
            self.provider = "openai"
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif model_name.startswith("gemini"):
            self.temperature = temperature
            self.provider = "gemini"
            self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        else:
            raise ValueError(f"Unsupported model: {model_name}")

    def chat(self, messages: list[dict], max_tokens=2000):
        if self.provider == "openai":
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            ).choices[0].message.content
        elif self.provider == "gemini":
            return self.client.models.generate_content(
                model=self.model,
                contents=messages[-1]["content"]
            ).text
