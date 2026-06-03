"""TaskFlow MVP — FastAPI 앱 엔트리포인트."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (테이블 등록)
from app.config import CORS_ORIGINS
from app.db import Base, engine
from app.errors import install_error_handlers
from app.routers import auth, messages, tasks, teams

TAGS_METADATA = [
    {"name": "Auth", "description": "회원가입·로그인·로그아웃·현재 사용자"},
    {"name": "Team", "description": "팀 생성·합류·조회·멤버·떠나기"},
    {"name": "Task", "description": "칸반 태스크 CRUD·상태 전이·필터"},
    {"name": "Chat", "description": "팀 채팅 — 5초 폴링(id 커서)·전송·삭제"},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="TaskFlow MVP API",
    version="0.1.0",
    description=(
        "소규모 팀용 칸반 + 실시간 채팅(5초 폴링) MVP.\n\n"
        "- 인증: JWT(24h, 갱신 없음) · bcrypt\n"
        "- 시간대: KST(+09:00)\n"
        "- 에러 응답 표준: `{ error: { code, message, meta? } }`\n"
        "- 모든 API는 `/api` 프리픽스 사용"
    ),
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

install_error_handlers(app)

# 18개 API는 /api 프리픽스 하위로 (정적 파일과 경로 충돌 방지)
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(teams.router)
api_router.include_router(tasks.router)
api_router.include_router(messages.router)


@api_router.get("/health", tags=["Meta"])
def health():
    return {"status": "ok"}


app.include_router(api_router)

# 프론트엔드 정적 파일 서빙 (동일 오리진). /api·/docs·/openapi.json 등록 이후 mount → catch-all
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
