from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PORT: int = 8080
    NETWORK_HOST: str = "node1"
    NETWORK_PORT: int = 9001
    USE_MOCK: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
