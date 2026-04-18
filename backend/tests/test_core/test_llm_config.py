"""Tests for the config-based LLM factory."""

import os
from unittest.mock import patch

import pytest


def test_load_config_finds_file():
    """load_config should parse config.yaml and resolve env vars."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key2"}):
        from src.core.llm import load_config

        config = load_config()
        assert "models" in config
        assert "agents" in config
        assert config["models"]["glm-flash"]["api_key"] == "test-key"
        assert config["models"]["claude-sonnet"]["api_key"] == "test-key2"


def test_load_config_env_var_resolution():
    """${VAR} syntax should be resolved from environment."""
    with patch.dict(os.environ, {"MY_TEST_KEY": "resolved-value"}):
        from src.core.llm import _resolve_env_vars

        data = {"key": "${MY_TEST_KEY}", "nested": {"url": "http://${MY_TEST_KEY}/path"}}
        result = _resolve_env_vars(data)
        assert result["key"] == "resolved-value"
        assert result["nested"]["url"] == "http://resolved-value/path"


def test_load_config_missing_env_var_raises():
    """Missing env var should raise a clear error."""
    from src.core.llm import _resolve_env_vars

    with pytest.raises(ValueError, match="NONEXISTENT_KEY"):
        _resolve_env_vars({"key": "${NONEXISTENT_KEY}"})


def test_get_llm_unknown_agent_raises():
    """get_llm with unknown agent name should raise with helpful message."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test", "ANTHROPIC_API_KEY": "test"}):
        from src.core.llm import get_llm, reload_config

        reload_config()
        with pytest.raises(ValueError, match="Unknown agent"):
            get_llm("nonexistent_agent")


def test_get_llm_returns_chat_model():
    """get_llm should return a ChatOpenAI instance for openai_compatible provider."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test-key", "ANTHROPIC_API_KEY": "test-key"}):
        from langchain_openai import ChatOpenAI

        from src.core.llm import get_llm, reload_config

        reload_config()
        llm = get_llm("achievement_analysis")
        assert isinstance(llm, ChatOpenAI)


def test_get_llm_anthropic_provider():
    """get_llm should return a ChatAnthropic instance for anthropic provider."""
    with patch.dict(os.environ, {"GLM_API_KEY": "test", "ANTHROPIC_API_KEY": "test-key"}):
        from langchain_anthropic import ChatAnthropic

        from src.core.llm import get_llm, reload_config

        reload_config()
        llm = get_llm("resume_update")
        assert isinstance(llm, ChatAnthropic)


def test_default_config_when_file_missing():
    """When config.yaml is missing, embedded defaults should be used."""
    import src.core.llm as llm_mod

    original = llm_mod._CONFIG_PATH
    llm_mod._CONFIG_PATH = "/nonexistent/config.yaml"
    try:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            config = llm_mod.load_config()
            assert "models" in config
            assert "agents" in config
    finally:
        llm_mod._CONFIG_PATH = original
