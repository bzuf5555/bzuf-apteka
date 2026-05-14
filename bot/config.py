from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    ANTHROPIC_API_KEY: str = ""

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "dorixona"

    WEBHOOK_HOST: str = ""
    WEBHOOK_SECRET: str = "dorixona_secret"

    SEARCH_RADIUS_KM: float = 5.0
    MAX_RESULTS: int = 10
    RATE_LIMIT_PER_MINUTE: int = 10
    BOT_ENV: str = "development"

    @property
    def admin_ids(self) -> list[int]:
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    @property
    def is_production(self) -> bool:
        return self.BOT_ENV == "production"

    @property
    def webhook_path(self) -> str:
        return f"/bot/{self.BOT_TOKEN}"

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_HOST}{self.webhook_path}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
