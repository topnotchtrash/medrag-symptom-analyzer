# core/llm_client.py
import os
from typing import List, Dict, Optional, Any

# Optional: Streamlit secrets support (does nothing outside Streamlit)
try:
    import streamlit as st  # type: ignore
    _st_available = True
except Exception:
    _st_available = False


# -------------------------
# Lightweight HTTP Clients
# -------------------------

class _MockLLM:
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"Mock analysis for: {last[:80]}..."


class _GroqLLM:
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        import requests  # local import to keep import cost low
        self._requests = requests
        self.api_key = api_key
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        """
        kwargs may include: max_tokens, top_p, frequency_penalty, presence_penalty, stop, seed, etc.
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": float(temperature),
        }
        # pass through any supported OpenAI-compatible params
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        r = self._requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


class _OpenAILLM:
    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str):
        import requests
        self._requests = requests
        self.api_key = api_key
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": float(temperature),
        }
        payload.update({k: v for k, v in kwargs.items() if v is not None})

        r = self._requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


# -------------------------
# Factory + Helpers
# -------------------------

def _get_secret(name: str) -> Optional[str]:
    """Priority: env var > Streamlit secrets > None"""
    val = os.getenv(name)
    if val:
        return str(val).strip()
    if _st_available:
        try:
            s = st.secrets.get(name, "")
            return str(s).strip() if s else None
        except Exception:
            pass
    return None


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
):
    """
    Returns an LLM client instance.

    Priority:
      - provider: explicit arg > LLM_PROVIDER env/secret > 'mock'
      - api_key:  explicit arg > ENV/secret > (required for real providers)
      - model:    explicit arg > ENV/secret > default per provider
    """
    prov = (provider or _get_secret("LLM_PROVIDER") or "mock").lower()

    if prov == "groq":
        key = (api_key or _get_secret("GROQ_API_KEY"))
        mdl = (model or _get_secret("GROQ_MODEL") or "llama-3.1-8b-instant")
        if not key:
            raise RuntimeError("Set GROQ_API_KEY")
        return _GroqLLM(key, mdl)

    if prov == "openai":
        key = (api_key or _get_secret("OPENAI_API_KEY"))
        mdl = (model or _get_secret("OPENAI_MODEL") or "gpt-4o-mini")
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY")
        return _OpenAILLM(key, mdl)

    # Default to mock for local/dev
    return _MockLLM()
