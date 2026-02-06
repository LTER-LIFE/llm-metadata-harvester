from openai import OpenAI
try:
    from google import genai
except ImportError:
    genai = None
from dotenv import load_dotenv
import os

load_dotenv()

class LLMClient:
    def __init__(self, model_name: str,
                 temperature: float = 0.0,
                 api_key: str = None, **kwargs):
        self.temperature = temperature
        if model_name.startswith("gpt"):
            self.model = model_name
            self.provider = "openai"
            key = api_key or os.getenv("OPENAI_API_KEY")
            self.client = OpenAI(api_key=key)
        elif model_name.startswith("gemini"):
            self.model = model_name
            if genai is None:
                raise ImportError("google package is required for Gemini models. Install it with: pip install google")
            self.provider = "gemini"
            key = api_key or os.getenv("GEMINI_API_KEY")
            self.client = genai.Client(api_key=key)
        elif model_name.startswith("surf"):
            # for surf models it should be named `surf-{actual_model_name}`
            self.provider = "surf"
            self.model = model_name.removeprefix("surf-")  # Remove 'surf-' prefix
            key = api_key or os.getenv("SURF_API_KEY")
            base_url = kwargs.get("base_url", "https://willma.surf.nl/api/v0")
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
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
            elif self.provider == "surf":
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens
                ).choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"LLM client response failed: Error from LLM provider:\n{e}") from e
