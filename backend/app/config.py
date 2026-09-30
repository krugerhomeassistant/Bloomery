"""Runtime settings, all overridable via BLOOMERY_* environment variables."""
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BLOOMERY_", env_file=".env", extra="ignore")

    data_dir: Path = Path("./data")
    secret_key: str = ""
    # "auto" = open only until the first account exists; "true" = always open; "false" = closed
    allow_registration: str = "auto"
    session_max_age_days: int = 30
    secure_cookies: bool = False  # set true behind HTTPS
    static_dir: Path = Path("./static")

    # AI defaults; overridden by in-app settings (Profile → AI assistant). See ai.PROVIDERS.
    ai_provider: str = "none"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout: float = 120.0

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.data_dir / 'bloomery.db'}"

    def resolved_secret(self) -> str:
        if self.secret_key:
            return self.secret_key
        self.data_dir.mkdir(parents=True, exist_ok=True)
        f = self.data_dir / "secret.key"
        if not f.exists():
            f.write_text(secrets.token_urlsafe(48))
            f.chmod(0o600)
        return f.read_text().strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
