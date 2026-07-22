from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hostname: str = 'localhost'
    port: int = 9998
    project_name: str = 'Whoosh'
    ssl_keyfile: str = '/etc/letsencrypt/live/example.com/privkey.pem'
    ssl_certfile: str = '/etc/letsencrypt/live/example.com/fullchain.pem'

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
    )
