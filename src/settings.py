from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    DEBUG: bool

    HOST: str
    PORT: int
    ACCESS_CODE: str

    DB_URL: str

    REDIS_URL: str
    REDIS_EXPIRE: int
    REDIS_POOL_SIZE: int
    REDIS_PREFIX: str


settings = Settings()
