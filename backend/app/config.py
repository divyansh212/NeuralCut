from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""      # server-side only, never sent to browser
    SUPABASE_JWT_SECRET: str = ""       # used to verify user JWTs
    STORAGE_BUCKET: str = "renders"

    # infra
    REDIS_URL: str = "redis://redis:6379/0"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # pipeline
    PROVIDER_MODE: str = "mock"         # "mock" | "live"

    # live provider keys (only needed when PROVIDER_MODE=live)
    OPENAI_API_KEY: str = ""
    REPLICATE_API_TOKEN: str = ""
    ELEVENLABS_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
