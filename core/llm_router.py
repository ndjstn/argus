
import logging
import requests
import json

class LLMRouter:
    """A router for large language models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LLMRouter")

    def route(self, provider: str, model: str, message: str) -> str:
        """Route a message to the appropriate model."""
        self.logger.info(f"Routing message to {provider} model: {model}")
        self.logger.debug(f"Message content: {message}")

        if provider == "Ollama":
            return self._call_ollama(model, message)
        elif provider == "OpenAI":
            return self._call_openai(model, message)
        elif provider == "Gemini":
            return self._call_gemini(model, message)
        elif provider == "Groq":
            return self._call_groq(model, message)
        elif provider == "Claude":
            return self._call_claude(model, message)
        else:
            self.logger.warning(f"Unknown provider: {provider}")
            return f"Unknown provider: {provider}"

    def _call_ollama(self, model: str, message: str) -> str:
        self.logger.info(f"Calling Ollama model: {model}")
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": message},
                stream=True
            )
            response.raise_for_status()
            full_response = ""
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    json_line = json.loads(decoded_line)
                    full_response += json_line.get("response", "")
            return full_response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            return f"Error calling Ollama API: {e}"
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding Ollama API response: {e}")
            return f"Error decoding Ollama API response: {e}"

    def _call_openai(self, model: str, message: str) -> str:
        self.logger.info(f"Calling OpenAI model: {model}")
        # Mock implementation
        return f"OpenAI response to: {message}"

    def _call_gemini(self, model: str, message: str) -> str:
        self.logger.info(f"Calling Gemini model: {model}")
        # Mock implementation
        return f"Gemini response to: {message}"

    def _call_groq(self, model: str, message: str) -> str:
        self.logger.info(f"Calling Groq model: {model}")
        # Mock implementation
        return f"Groq response to: {message}"

    def _call_claude(self, model: str, message: str) -> str:
        self.logger.info(f"Calling Claude model: {model}")
        # Mock implementation
        return f"Claude response to: {message}"
