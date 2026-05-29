from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8')

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_USER_IDS: str = ""

    # AI Provider
    AI_PROVIDER: Literal['gemini', 'claude',
                         'openai', 'groq', 'deepseek', 'openrouter'] = 'groq'

    GEMINI_API_KEY: str | None = None
    CLAUDE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    DEEPSEEK_API_KEY: str | None = None
    OPENROUTER_API_KEY: str | None = None

    # Google Services
    GOOGLE_DRIVE_FOLDER_ID: str = ""
    # OAuth 2.0 (приоритет) или Service Account
    GOOGLE_OAUTH_CREDENTIALS: str | None = None
    GOOGLE_SERVICE_ACCOUNT_FILE: str | None = 'credentials/google_service_account.json'

    # Scheduler
    SCHEDULE_CRON: str = '0 9 */3 * *'

    # Application Settings
    MODE: Literal['DEV', 'TEST', 'PROD'] = 'PROD'
    LOG_LEVEL: Literal['DEBUG', 'INFO',
                       'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'

    # Claude Model Settings
    CLAUDE_MODEL: str = 'claude-3-5-haiku-20241022'  # Fastest and cheapest
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.7

    # OpenAI Model Settings (Production)
    OPENAI_MODEL: str = 'gpt-4o-mini'  # Быстрая и качественная модель для прода
    OPENAI_MAX_TOKENS: int = 16384
    OPENAI_TEMPERATURE: float = 0.7

    # Gemini Model Settings (Production)
    GEMINI_MODEL: str = 'gemini-2.0-flash-exp'  # Самая быстрая и качественная
    GEMINI_MAX_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.7

    # Groq (OpenAI-совместимый API: https://console.groq.com)
    GROQ_BASE_URL: str = 'https://api.groq.com/openai/v1'
    GROQ_MODEL: str = 'llama-3.3-70b-versatile'
    GROQ_MAX_TOKENS: int = 8192
    GROQ_TEMPERATURE: float = 0.7

    # DeepSeek (OpenAI-совместимый API: https://platform.deepseek.com)
    DEEPSEEK_BASE_URL: str = 'https://api.deepseek.com'
    DEEPSEEK_MODEL: str = 'deepseek-chat'
    DEEPSEEK_MAX_TOKENS: int = 4096
    DEEPSEEK_TEMPERATURE: float = 0.7

    # OpenRouter (агрегатор моделей: https://openrouter.ai)
    OPENROUTER_BASE_URL: str = 'https://openrouter.ai/api/v1'
    OPENROUTER_MODEL: str = 'openai/gpt-oss-120b:free'
    OPENROUTER_MAX_TOKENS: int = 8192
    OPENROUTER_TEMPERATURE: float = 0.7

    # News Parser Settings (Production)
    NEWS_DAYS_BACK: int = 7
    NEWS_MAX_ITEMS: int = 100  # Увеличено для прода

    # Generation Limits (Production - увеличены для качества)
    INFOREASONS_MIN: int = 15
    INFOREASONS_MAX: int = 25
    ANGLES_MIN: int = 30
    ANGLES_MAX: int = 50
    HEADLINES_MIN: int = 50
    HEADLINES_MAX: int = 80
    TOP_IDEAS_COUNT: int = 10

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
        elif self.AI_PROVIDER == 'deepseek':
            if not self.DEEPSEEK_API_KEY:
                raise ValueError(
                    "DEEPSEEK_API_KEY is required when AI_PROVIDER=deepseek")
            return self.DEEPSEEK_API_KEY
        elif self.AI_PROVIDER == 'openrouter':
            if not self.OPENROUTER_API_KEY:
                raise ValueError(
                    "OPENROUTER_API_KEY is required when AI_PROVIDER=openrouter")
            return self.OPENROUTER_API_KEY
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
        elif self.AI_PROVIDER == 'deepseek':
            return self.DEEPSEEK_MODEL
        elif self.AI_PROVIDER == 'openrouter':
            return self.OPENROUTER_MODEL
        else:
            raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")

    @computed_field
    @property
    def ACTIVE_AI_TEMPERATURE(self) -> float:
        if self.AI_PROVIDER == 'claude':
            return self.CLAUDE_TEMPERATURE
        elif self.AI_PROVIDER == 'openai':
            return self.OPENAI_TEMPERATURE
        elif self.AI_PROVIDER == 'gemini':
            return self.GEMINI_TEMPERATURE
        elif self.AI_PROVIDER == 'groq':
            return self.GROQ_TEMPERATURE
        elif self.AI_PROVIDER == 'deepseek':
            return self.DEEPSEEK_TEMPERATURE
        elif self.AI_PROVIDER == 'openrouter':
            return self.OPENROUTER_TEMPERATURE
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
        if self.AI_PROVIDER == 'deepseek':
            return self.DEEPSEEK_MAX_TOKENS
        if self.AI_PROVIDER == 'openrouter':
            return self.OPENROUTER_MAX_TOKENS
        raise ValueError(f"Unknown AI_PROVIDER: {self.AI_PROVIDER}")


settings = Settings()
