from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    database_url: str = "postgresql+psycopg://opap:opap@localhost:5432/opap"
    api_key: str = Field(default="dev-change-me", validation_alias="OPAP_API_KEY")
    public_base_url: str = "https://verify.opap.example"
    sql_echo: bool = False

    # Pluggable Signer & HSM / KMS configuration
    signer_provider: str = Field(default="env", validation_alias="OPAP_SIGNER_PROVIDER")
    signing_private_key_hex: str | None = Field(default=None, validation_alias="OPAP_SIGNING_PRIVATE_KEY_HEX")
    signing_key_path: str | None = Field(default=None, validation_alias="OPAP_SIGNING_KEY_PATH")
    kms_key_id: str | None = Field(default=None, validation_alias="OPAP_KMS_KEY_ID")
    kms_region: str | None = Field(default=None, validation_alias="OPAP_KMS_REGION")
    kms_mock: bool = Field(default=False, validation_alias="OPAP_KMS_MOCK")
    pkcs11_lib_path: str | None = Field(default=None, validation_alias="OPAP_PKCS11_LIB_PATH")
    pkcs11_slot_id: int | None = Field(default=0, validation_alias="OPAP_PKCS11_SLOT_ID")
    pkcs11_key_label: str | None = Field(default="opap-ed25519", validation_alias="OPAP_PKCS11_KEY_LABEL")


@lru_cache
def get_settings() -> Settings:
    return Settings()

