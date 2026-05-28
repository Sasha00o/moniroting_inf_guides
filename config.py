from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    ADMIN_USER_IDS: str

    # AI Provider
    AI_PROVIDER: Literal['gemini', 'claude', 'openai', 'groq']

    # AI API Keys (only one is required based on AI_PROVIDER)
    GEMINI_API_KEY: str | None = None
    CLAUDE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None

    # Google Services
    GOOGLE_DRIVE_FOLDER_ID: str
    GOOGLE_SERVICE_ACCOUNT_FILE: str = 'credentials/google_service_account.json'

    # Scheduler
    SCHEDULE_CRON: str = '0 9 */3 * *'

    # Application Settings
    MODE: Literal['DEV', 'TEST', 'PROD'] = 'DEV'
    LOG_LEVEL: Literal['DEBUG', 'INFO',
                       'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'

    # Claude Model Settings
    CLAUDE_MODEL: str = 'claude-3-5-haiku-20241022'  # Fastest and cheapest
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7

    # OpenAI Model Settings
    OPENAI_MODEL: str = 'gpt-4o-mini'
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7

    # Gemini Model Settings
    GEMINI_MODEL: str = 'gemini-1.5-flash'
    GEMINI_MAX_TOKENS: int = 4096
    GEMINI_TEMPERATURE: float = 0.7

    # Groq (OpenAI-совместимый API: https://console.groq.com)
    GROQ_BASE_URL: str = 'https://api.groq.com/openai/v1'
    GROQ_MODEL: str = 'llama-3.3-70b-versatile'
    GROQ_MAX_TOKENS: int = 4096
    GROQ_TEMPERATURE: float = 0.7

    # News Parser Settings
    NEWS_DAYS_BACK: int = 7  # How many days back to parse news
    NEWS_MAX_ITEMS: int = 50  # Maximum news items to collect

    # Report Generation Settings
    INFOREASONS_MIN: int = 10
    INFOREASONS_MAX: int = 20
    ANGLES_MIN: int = 20
    ANGLES_MAX: int = 30
    HEADLINES_MIN: int = 30
    HEADLINES_MAX: int = 50
    TOP_IDEAS_COUNT: int = 5

    @computed_field
    @property
    def ADMIN_USER_IDS_LIST(self) -> list[int]:
        """Parse comma-separated admin user IDs into a list of integers."""
        return [int(uid.strip()) for uid in self.ADMIN_USER_IDS.split(',') if uid.strip()]

    @computed_field
    @property
    def ACTIVE_AI_KEY(self) -> str:
        """Get the active AI API key based on AI_PROVIDER."""
        if self.AI_PROVIDER == 'claude':
            if not self.CLAUDE_API_KEY:
                raise ValueError(
                    "CLAUDE_API_KEY is required when AI_PROVIDER=claude")
            return self.CLAUDE_API_KEY
        elif self.AI_PROVIDER == 'openai':
            if not self.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY is required when AI_PROVIDER=openai")
            return self.OPENAI_API_KEY
        elif self.AI_PROVIDER == 'gemini':
            if not self.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required when AI_PROVIDER=gemini")
            return self.GEMINI_API_KEY
        elif self.AI_PROVIDER == 'groq':
            if not self.GROQ_API_KEY:
                raise ValueError(
                    "GROQ_API_KEY is required when AI_PROVIDER=groq")
            return self.GROQ_API_KEY
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")

    @computed_field
    @property
    def ACTIVE_AI_MODEL(self) -> str:
        """Get the active AI model based on AI_PROVIDER."""
        if self.AI_PROVIDER == 'claude':
            return self.CLAUDE_MODEL
        elif self.AI_PROVIDER == 'openai':
            return self.OPENAI_MODEL
        elif self.AI_PROVIDER == 'gemini':
            return self.GEMINI_MODEL
        elif self.AI_PROVIDER == 'groq':
            return self.GROQ_MODEL
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")

    @computed_field
    @property
    def ACTIVE_AI_TEMPERATURE(self) -> float:
        """Get the active AI temperature based on AI_PROVIDER."""
        if self.AI_PROVIDER == 'claude':
            return self.CLAUDE_TEMPERATURE
        elif self.AI_PROVIDER == 'openai':
            return self.OPENAI_TEMPERATURE
        elif self.AI_PROVIDER == 'gemini':
            return self.GEMINI_TEMPERATURE
        elif self.AI_PROVIDER == 'groq':
            return self.GROQ_TEMPERATURE
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")

    @computed_field
    @property
    def ACTIVE_AI_MAX_TOKENS(self) -> int:
        """Максимум токенов ответа для активного провайдера."""
        if self.AI_PROVIDER == 'claude':
            return self.CLAUDE_MAX_TOKENS
        if self.AI_PROVIDER == 'openai':
            return self.OPENAI_MAX_TOKENS
        if self.AI_PROVIDER == 'gemini':
            return self.GEMINI_MAX_TOKENS
        if self.AI_PROVIDER == 'groq':
            return self.GROQ_MAX_TOKENS
        raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")


settings = Settings()
