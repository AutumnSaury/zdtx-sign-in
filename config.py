from pydantic import BaseSettings


class Config(BaseSettings):
    zdtx_device_token: str
    zdtx_phone: str
    zdtx_password: str
    zdtx_college_prefix: str
    zdtx_health_json: dict
    zdtx_health_json_meta: dict
    class Config:
        extra = "ignore"