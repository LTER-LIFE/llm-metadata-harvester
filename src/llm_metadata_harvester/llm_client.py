"""
MIT License

Copyright (c) 2025 LTER-LIFE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from openai import OpenAI
try:
    from google import genai
except ImportError:
    genai = None
from dotenv import load_dotenv
import os

load_dotenv()

class LLMClient:
    def __init__(self, model_name: str, temperature: float = 0.0, api_key: str = None):
        self.model = model_name
        if model_name.startswith("gpt"):
            self.temperature = temperature
            self.provider = "openai"
            key = api_key or os.getenv("OPENAI_API_KEY")
            self.client = OpenAI(api_key=key)
        elif model_name.startswith("gemini"):
            if genai is None:
                raise ImportError("google package is required for Gemini models. Install it with: pip install google")
            self.temperature = temperature
            self.provider = "gemini"
            key = api_key or os.getenv("GEMINI_API_KEY")
            self.client = genai.Client(api_key=key)

        else:
            raise ValueError(f"Unsupported LLM: {model_name}")

    def chat(self, messages: list[dict], max_tokens=2000):
        try:
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
        except Exception as e:
            raise RuntimeError(f"LLM client response failed: Error from LLM provider:\n{e}") from e
