"""공통 유틸 — KST 시간대."""
from datetime import datetime, timedelta, timezone

# 결정: 서버·클라이언트 모두 KST. UTC 변환 없음. 직렬화 시 +09:00 오프셋 명시.
KST = timezone(timedelta(hours=9))


def now_kst() -> datetime:
    """DB 저장용 KST '벽시계' 시각 (naive).

    tz-aware 값을 `timestamp without time zone`(Postgres) 컬럼에 넣으면
    세션 TZ(UTC)로 변환되어 9시간 어긋난다. SQLite/Postgres 양쪽에서
    동일하게 KST 벽시계를 그대로 저장하기 위해 naive로 둔다.
    응답 직렬화 시 schemas에서 +09:00 오프셋을 다시 부여한다.
    """
    return datetime.now(KST).replace(tzinfo=None)
