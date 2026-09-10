import os
from dotenv import load_dotenv
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when Cardfolio is missing required configuration."""


# Build the path from this file so configuration works regardless of the
# directory from which Cardfolio is launched.
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"

# A real environment variable takes priority over the local file. Production
# can therefore put in secrets without depending on a `.env` file.
load_dotenv(dotenv_path=ENV_FILE, override=False)

def get_database_url() -> str:
    """Return the database address used by Cardfolio."""

    database_url = os.getenv("DATABASE_URL", "").strip()

    if not database_url:
        raise ConfigurationError(
            "DATABASE_URL is not configured. "
            "Add it to backend/.env or provide it as an environment variable."
        )

    return database_url
