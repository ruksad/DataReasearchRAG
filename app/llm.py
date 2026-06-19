from langchain_core.language_models import BaseChatModel
from app import config
import logging

logger= logging.getLogger(__name__)
def get_llm() -> BaseChatModel:
    """Return a chat model for the configured LLM_PROVIDER."""
    provider = config.LLM_PROVIDER.lower()
    logger.info(f"LLM PROVIDER: {provider}")
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=config.OLLAMA_BASE_URL,
            model=config.OLLAMA_MODEL,
            temperature=0,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=config.ANTHROPIC_API_KEY,
            model=config.ANTHROPIC_MODEL,
            temperature=0,
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=config.OPENAI_API_KEY,
            model=config.OPENAI_MODEL,
            temperature=0,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER '{config.LLM_PROVIDER}'. "
        "Choose from: ollama, anthropic, openai"
    )
