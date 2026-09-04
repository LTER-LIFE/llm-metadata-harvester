import json
import os
import re

from openai import OpenAI
try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None
from dotenv import load_dotenv

load_dotenv()

# Native context sizes (input + output). Override Surf via SURF_CONTEXT_LIMIT.
MODEL_CONTEXT_LIMITS = {
    "openai": 128_000,
    "gemini": 1_048_576,
    "surf": {
        "default": 32_768,
        "qwen": 262_144,
        "gpt-oss": 128_000,
    },
}

DEFAULT_STRUCTURED_MAX_OUTPUT = {
    "openai": 8_192,
    "gemini": 8_192,
    "surf": 32_768,
}


def _parse_json_content(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


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
                api_key=key,
                base_url=base_url
            )
        else:
            raise ValueError(f"Unsupported LLM: {model_name}")

        self.context_limit = self._resolve_context_limit()
        self.structured_max_output_tokens = self._resolve_structured_max_output_tokens()

    def _resolve_context_limit(self) -> int:
        if self.provider == "surf":
            env_limit = os.getenv("SURF_CONTEXT_LIMIT")
            if env_limit:
                return int(env_limit)
            model_lower = self.model.lower()
            surf_limits = MODEL_CONTEXT_LIMITS["surf"]
            for key, limit in surf_limits.items():
                if key != "default" and key in model_lower:
                    return limit
            return surf_limits["default"]
        return MODEL_CONTEXT_LIMITS[self.provider]

    def _resolve_structured_max_output_tokens(self) -> int:
        if self.provider == "surf":
            env_limit = os.getenv("SURF_MAX_OUTPUT_TOKENS")
            if env_limit:
                return int(env_limit)
        return DEFAULT_STRUCTURED_MAX_OUTPUT[self.provider]

    def get_chunk_token_limit(
        self,
        output_reserve: int | None = None,
        prompt_reserve: int = 12_000,
    ) -> int:
        """Max input tokens per chunk, leaving room for prompt and model output."""
        output_reserve = output_reserve or self.structured_max_output_tokens
        return max(4_000, self.context_limit - output_reserve - prompt_reserve)

    def _surf_create(self, *, max_tokens: int, **kwargs):
        """Create a Surf/Willma chat completion, disabling Qwen thinking by default."""
        model_lower = self.model.lower()
        if "qwen" in model_lower or "devstral" in model_lower:
            enable_thinking = os.getenv("SURF_ENABLE_THINKING", "false").lower() == "true"
            kwargs["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": enable_thinking},
            }
        return self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @staticmethod
    def _format_gemini_contents(messages: list[dict]) -> str:
        parts = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "system":
                parts.append(f"System: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")
            else:
                parts.append(content)
        return "\n\n".join(parts)

    def chat(self, messages: list[dict], max_tokens=2000):
        try:
            if self.provider == "openai":
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                ).choices[0].message.content
            elif self.provider == "gemini":
                return self.client.models.generate_content(
                    model=self.model,
                    contents=messages[-1]["content"],
                ).text
            elif self.provider == "surf":
                return self._surf_create(
                    messages=messages,
                    max_tokens=max_tokens,
                ).choices[0].message.content
        except Exception as e:
            raise RuntimeError(
                f"LLM client response failed: Error from LLM provider:\n{e}"
            ) from e

    def chat_structured(
        self,
        messages: list[dict],
        schema_name: str,
        schema: dict,
        max_tokens: int = 2000,
    ) -> dict:
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=max_tokens,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": schema_name,
                            "strict": True,
                            "schema": schema,
                        },
                    },
                )
                return _parse_json_content(response.choices[0].message.content)

            if self.provider == "surf":
                # Willma/Qwen: json_object mode + schema described in the prompt.
                response = self._surf_create(
                    messages=messages,
                    max_tokens=max(max_tokens, self.structured_max_output_tokens),
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError(
                        "Surf model returned empty content. "
                        f"Finish reason: {response.choices[0].finish_reason}"
                    )
                return _parse_json_content(content)

            if self.provider == "gemini":
                if genai_types is None:
                    raise ImportError(
                        "google package is required for Gemini models. "
                        "Install it with: pip install google-genai"
                    )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=self._format_gemini_contents(messages),
                    config=genai_types.GenerateContentConfig(
                        temperature=self.temperature,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                        response_schema=schema,
                    ),
                )
                if getattr(response, "parsed", None) is not None:
                    return response.parsed
                return _parse_json_content(response.text)

            raise ValueError(f"Unsupported provider for structured output: {self.provider}")
        except Exception as e:
            raise RuntimeError(
                f"LLM structured response failed: Error from LLM provider:\n{e}"
            ) from e
