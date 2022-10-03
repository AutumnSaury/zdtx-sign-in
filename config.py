from pydantic import BaseSettings


class Config(BaseSettings):
    zdtx_device_token: str
    zdtx_phone: str
    zdtx_password: str
    zdtx_college_prefix: str
    zdtx_health_json: str
    class Config:
        extra = "ignore"