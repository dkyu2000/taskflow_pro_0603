"""Vercel Serverless 진입점 — ASGI app(`app`)을 노출.

서버리스는 lifespan 이벤트가 보장되지 않으므로, 콜드스타트 시 import 시점에
테이블 생성을 한 번 수행한다(idempotent). 운영 DB는 DATABASE_URL(Neon).
"""
from app import models  # noqa: F401  (테이블 등록)
from app.db import Base, engine

Base.metadata.create_all(bind=engine)

from app.main import app  # noqa: E402  (ASGI app — Vercel @vercel/python이 인식)

__all__ = ["app"]
