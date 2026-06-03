"""환경 설정 — DATABASE_URL 등은 환경변수로만 전환."""
import os

# 로컬 기본값은 SQLite 파일, 운영은 Neon(PostgreSQL)을 DATABASE_URL로 주입
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./taskflow.db")

# JWT — 24h 만료, 갱신 없음, HS256
JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALG: str = "HS256"
JWT_EXPIRE_HOURS: int = 24

# CORS 허용 도메인 (운영 도메인은 환경변수로 추가)
CORS_ORIGINS: list[str] = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8000,http://localhost:3000,http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if o.strip()
]
