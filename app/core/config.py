import pathlib
import json
import threading
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, HttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class InternalApiCredential(BaseModel):
    user_name: str
    password: str

class AuthConfig(BaseModel):
    access_secret_key: str
    refresh_secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1440
    access_token_type: str = "Bearer"

class OTELGrpcExporterConfig(BaseModel):
    exporter_name: str = "grpc"
    exporter_url: str = "http://localhost:4317"
    insecure: bool = True
    credentials: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None

class OTELConsoleExporterConfig(BaseModel):
    metric_exporter_name: str = "console"

class OTELConfig(BaseModel):
    is_enabled: bool = False
    app_name: str = "tailor-app"
    otel_exporter: Union[OTELConsoleExporterConfig, OTELGrpcExporterConfig] = Field(default_factory=OTELGrpcExporterConfig)
    otel_exporter_interval_millis: float = 60000
    otel_exporter_timeout_millis: float = 30000
    environment: str = "PROD"
    excluded_urls: List[str] = []

class Settings(BaseSettings):
    db_url: str
    data_base: str
    ROOT_LOG_LEVEL: str = "INFO"
    APP_LOG_LEVEL: str = "INFO"
    SRV_LOG_FILE_LOCATION: str = "logs/app.log"
    ACCESS_LOG_FILE_LOCATION: str = "logs/access.log"
    LOG_FILE_SIZE_BYTE: int = 10485760
    LOG_FILE_BACKUP_COUNT: int = 5
    COUNTRY_INDIA_LIST: Any = Field(default_factory=dict)

    @field_validator("COUNTRY_INDIA_LIST", mode="before")
    @classmethod
    def parse_country_list(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v

    # model_config = SettingsConfigDict(
    #     env_file=pathlib.Path(__file__).resolve().parent.parent.parent / ".env",
    #     extra="ignore"
    # )

    model_config = SettingsConfigDict(
        env_file=f"{pathlib.Path(__file__).resolve().parent}/config.env"
    )


settings = Settings()

# Runtime Secrets (Enriched from DB)
class AppSecret(BaseModel):
    internal_api_credential: InternalApiCredential
    auth_config: AuthConfig
    otp_expiry_seconds: int = 300

    class Config:
        populate_by_name = True

_app_secret: Optional[AppSecret] = None
_app_secret_lock = threading.Lock()

def enrich_app_secret(data: Dict[str, Any]):
    global _app_secret
    with _app_secret_lock:
        if _app_secret is None:
            try:
                _app_secret = AppSecret(**data)
            except ValidationError as e:
                error_details = []
                for error in e.errors():
                    loc = " -> ".join(str(l) for l in error.get("loc", []))
                    msg = error.get("msg")
                    error_details.append(f"[{loc}]: {msg}")
                
                details_str = "\n".join(error_details)
                logger.critical(f"Invalid app_secret configuration in MongoDB:\n{details_str}")
                raise RuntimeError(f"Startup failed: Invalid AppSecret structure.")

def get_app_secret() -> AppSecret:
    if _app_secret is None:
        raise RuntimeError("AppSecret not enriched")
    return _app_secret
