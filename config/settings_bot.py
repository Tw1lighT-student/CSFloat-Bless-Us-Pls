from pathlib import Path
from pydantic import (
    Field
)
from pydantic_settings import BaseSettings, SettingsConfigDict

unborn_tier_1_id = 7211671075
ankor_id = 1225455200

class Config(BaseSettings):
    """Загружаем чувствительные данные (У нас из чувствительного только API-key телеграмма)"""
    telegram_api_key: str = Field(validation_alias='telegram_api_key')

    _env_path = Path(__file__).resolve().parent / '.env'
    model_config = SettingsConfigDict(env_file=str(_env_path),  # path to your .env
                                      env_file_encoding="utf-8",
                                      extra="ignore"  # extra keys in .env will be ignored
                                      )
bot_config = Config()