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

    # AI: none | ollama | openai | anthropic  (openai = any OpenAI-compatible endpoint)
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

    @property
    def ai_defaults(self) -> tuple[str, str]:
        """(base_url, model) with provider-specific defaults."""
        p = self.ai_provider.lower()
        base = self.ai_base_url
        model = self.ai_model
        if p == "ollama":
            base = base or "http://ollama:11434/v1"
            model = model or "llama3.2:3b"
        elif p == "openai":
            base = base or "https://api.openai.com/v1"
            model = model or "gpt-4o-mini"
        elif p == "anthropic":
            base = base or "https://api.anthropic.com"
            model = model or "claude-sonnet-5-5"
        return base.rstrip("/"), model


@lru_cache
def get_settings() -> Settings:
    return Settings()
