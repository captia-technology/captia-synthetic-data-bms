"""Configuration loaded from env vars with Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BMS_",
        env_file=".env",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8120
    health_port: int = 8121
    log_level: str = "INFO"

    domain_id: str = "bms_classrooms"
    n_aulas: int = 10
    seed: int = 42

    default_config_path: Path = Path("/app/config/projects/bms_v1_demo.yaml")
    output_dir: Path = Path("/app/output")
    backfill_default_days: int = 30
    faults_enabled: bool = False

    api_token: str = ""

    mqtt_host: str = "mosquitto"
    mqtt_port: int = 1883
    mqtt_qos: int = 1

    captia_env: str = "dev"
    captia_tenant: str = "default"
    captia_site: str = "ies_simarro"

    cors_allow_origins: str = "http://localhost:3001,http://localhost:8120"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Útil para tests que cambian env vars y necesitan recargar."""
    get_settings.cache_clear()
