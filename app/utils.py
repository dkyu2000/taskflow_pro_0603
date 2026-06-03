"""공통 유틸 — KST 시간대."""
from datetime import datetime, timedelta, timezone

# 결정: 서버·클라이언트 모두 KST. UTC 변환 없음. 직렬화 시 +09:00 오프셋 명시.
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """KST 기준 현재 시각(tz-aware)."""
    return datetime.now(KST)
