"""Application configuration settings."""


from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application settings
    APP_NAME: str = "FastAPI Elasticsearch Demo"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Elasticsearch settings
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: str | None = None
    ELASTICSEARCH_PASSWORD: str | None = None
    ELASTICSEARCH_USE_SSL: bool = False
    ELASTICSEARCH_INDEX_PREFIX: str = "fastapi-logs"

    # Kibana settings
    KIBANA_HOST: str = "localhost"
    KIBANA_PORT: int = 5601

    # API settings
    API_V1_STR: str = "/api/v1"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
