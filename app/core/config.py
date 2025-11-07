from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GOOGLE_API_KEY: str
    mcp_config_path: str = "app/mcp/config/mcp_config.json"
    PPLX_API_KEY: str
    GOOGLE_CREDENTIALS_PATH: str
    GOOGLE_TOKEN_PATH: str
    
    class Config:
    # Load environment variables from a local .env file in the project root
        env_file = ".env"
        env_file_encoding = "utf-8"

# Export a singleton settings instance for use across the app
settings = Settings()  # type: ignore