
import logging
import requests
import json
import os
import openai

class LLMRouter:
    """A router for large language models."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing LLMRouter")
        self.openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def route(self, provider: str, model: str, message: str, history: list) -> str:
        """Route a message to the appropriate model."""
        self.logger.info(f"Routing message to {provider} model: {model}")
        self.logger.debug(f"Message content: {message}")
        self.logger.debug(f"Conversation history: {history}")

        if provider == "Ollama":
            return self._call_ollama(model, message, history)
        elif provider == "OpenAI":
            return self._call_openai(model, message, history)
        elif provider == "Gemini":
            return self._call_gemini(model, message, history)
        elif provider == "Groq":
            return self._call_groq(model, message, history)
        elif provider == "Claude":
            return self._call_claude(model, message, history)
        else:
            self.logger.warning(f"Unknown provider: {provider}")
            return f"Unknown provider: {provider}"

    def _call_ollama(self, model: str, message: str, history: list) -> str:
        self.logger.info(f"Calling Ollama model: {model}")
        messages = history + [{"role": "user", "content": message}]
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={"model": model, "messages": messages, "stream": True},
            )
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    json_line = json.loads(decoded_line)
                    yield json_line["message"]["content"]
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Ollama API: {e}")
            yield f"Error calling Ollama API: {e}"

    def _call_openai(self, model: str, message: str, history: list) -> str:
        self.logger.info(f"Calling OpenAI model: {model}")
        messages = history + [{"role": "user", "content": message}]
        try:
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                yield chunk.choices[0].delta.content or ""
        except Exception as e:
            self.logger.error(f"Error calling OpenAI API: {e}")
            yield f"Error calling OpenAI API: {e}"

    def _call_gemini(self, model: str, message: str, history: list) -> str:
        self.logger.info(f"Calling Gemini model: {model}")
        # Mock implementation
        yield f"Gemini response to: {message}"

    def _call_groq(self, model: str, message: str, history: list) -> str:
        self.logger.info(f"Calling Groq model: {model}")
        # Mock implementation
        yield f"Groq response to: {message}"

    def _call_claude(self, model: str, message: str, history: list) -> str:
        self.logger.info(f"Calling Claude model: {model}")
        # Mock implementation
        yield f"Claude response to: {message}"
