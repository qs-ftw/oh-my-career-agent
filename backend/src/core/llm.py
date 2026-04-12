"""Multi-provider LLM factory.

Provides a single entry-point `get_llm` that returns a langchain ChatModel
configured for the requested provider.  Only the providers whose API keys
are present in settings will work at runtime.
"""

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from src.core.config import settings

_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "gemini": "gemini-2.0-flash",
}

_PROVIDER_TEMPERATURES: dict[str, float] = {
    "openai": 0.3,
    "anthropic": 0.3,
    "gemini": 0.3,
}


def get_llm(provider: str, model: str | None = None):
    """Return a langchain ChatModel for the given provider.

    Parameters
    ----------
    provider:
        One of ``"openai"``, ``"anthropic"``, or ``"gemini"``.
    model:
        Optional model identifier.  When *None* the provider-specific
        default from ``_DEFAULT_MODELS`` is used.

    Returns
    -------
    A langchain chat model instance ready for ``.invoke()`` / ``.ainvoke()``.
    """
    provider = provider.lower()
    model = model or _DEFAULT_MODELS.get(provider, "")
    temperature = _PROVIDER_TEMPERATURES.get(provider, 0.3)

    if provider == "openai":
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY or None,
        )

    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            api_key=settings.ANTHROPIC_API_KEY or None,
        )

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.GEMINI_API_KEY or None,
        )

    raise ValueError(
        f"Unsupported LLM provider: {provider!r}. "
        f"Supported providers: {', '.join(_DEFAULT_MODELS)}"
    )
