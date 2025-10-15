import os
from typing import Optional, Literal


class Settings:
    def __init__(self) -> None:
        self.app_name: str = "AI와 함께 놀며 사랑을 채우는 삶"
        self.debug: bool = True
        self.timezone: str = "Asia/Seoul"

        # 환경 설정 (dev, main)
        self.app_env: Literal["dev", "main"] = "dev"

        # 환경 변수에서 값 가져오기
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.debug = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
        self.timezone = os.getenv("TIMEZONE", self.timezone)

        # APP_ENV 환경변수 처리
        env_value = os.getenv("APP_ENV", "dev").lower()
        if env_value in ("dev", "main"):
            self.app_env = env_value  # type: ignore
        else:
            self.app_env = "dev"

        # 환경에 따른 데이터베이스 URL 설정
        # DATABASE_URL이 명시적으로 지정된 경우 우선 사용
        custom_db_url = os.getenv("DATABASE_URL")
        if custom_db_url:
            self.database_url: str = custom_db_url
        else:
            # 환경별 기본 DB 경로
            if self.app_env == "main":
                self.database_url = "sqlite:///./data/app.db"
            else:  # dev
                self.database_url = "sqlite:///./data/app_dev.db"


settings = Settings()
