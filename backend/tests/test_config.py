import pytest

from app.config import (
    ConfigurationError,
    get_pokemon_tcg_api_key,
)


def test_get_pokemon_tcg_api_key_reads_environment(monkeypatch):
    monkeypatch.setenv("POKEMON_TCG_API_KEY", "test-api-key")

    assert get_pokemon_tcg_api_key() == "test-api-key"


def test_get_pokemon_tcg_api_key_explains_missing_configuration(monkeypatch):
    monkeypatch.delenv("POKEMON_TCG_API_KEY", raising=False)

    with pytest.raises(
        ConfigurationError,
        match="POKEMON_TCG_API_KEY is not configured",
    ):
        get_pokemon_tcg_api_key()