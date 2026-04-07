import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8787

    # TiDB Cloud Zero
    tidb_connection_string: str = ""

    # Agnes AI via ZenMux (OpenAI-compatible)
    zenmux_api_key: str = ""
    zenmux_base_url: str = "https://zenmux.ai/api/v1"
    zenmux_model: str = "sapiens-ai/agnes-1.5-pro"

    # Bright Data SERP API
    brightdata_api_key: str = ""
    brightdata_serp_zone: str = ""

    # Mem9 (self-hosted mnemo-server)
    mem9_api_key: str = ""
    mem9_base_url: str = "http://localhost:8080"

    # User config (injected into AI prompts)
    user_role: str = "Engineering Manager"
    user_team_context: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
