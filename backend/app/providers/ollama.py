
import httpx

from app.core.config import get_settings


class OllamaError(RuntimeError):
    """Raised when Ollama cannot complete a request."""


class OllamaProvider:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.model = self.settings.ollama_model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        if not prompt.strip():
            raise ValueError("Prompt must not be empty.")

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.ollama_timeout_seconds
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            result = data.get("response", "").strip()

            if not result:
                raise OllamaError(
                    "Ollama returned an empty response."
                )

            return result

        except httpx.HTTPError as exc:
            raise OllamaError(
                "Could not generate a response using Ollama. "
                "Check that Ollama is running and the model is available."
            ) from exc
