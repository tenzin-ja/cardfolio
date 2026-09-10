import pytest

from app.config import ConfigurationError, get_database_url


def test_get_database_url_reads_environment(monkeypatch):
    # This only checks configuration; it doesn't connect to the database.
    database_url = (
        "postgresql+psycopg://test_user:test_password"
        "@localhost:5432/cardfolio_test"
    )
    monkeypatch.setenv("DATABASE_URL", database_url)

    assert get_database_url() == database_url


def test_get_database_url_explains_missing_configuration(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(
        ConfigurationError,
        match="DATABASE_URL is not configured",
    ):
        get_database_url()