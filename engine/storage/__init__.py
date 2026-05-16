"""SQLite 기반 익명 사용자 영구 저장.

설계 원칙:
  - **익명 ID** (UUID v4, 쿠키/localStorage 보관) — 회원가입 불필요
  - **민감정보 최소 저장** (꿈 일기·임상 척도만)
  - **사용자 삭제권** (`DELETE /api/user/me`) — 즉시 모든 데이터 파기
  - **단일 파일 SQLite** — Railway 컨테이너 안 `data/app.db`
  - **표준 라이브러리만 사용** (sqlite3) — 새 의존성 0

스키마 6 테이블:
  users         — 익명 ID + 가입 시각
  dream_diary   — Schredl 표준 일기 (#22)
  clinical_log  — 임상 척도 채점 결과 (#23·#26 종단)
  irt_session   — IRT 6단계 워크플로 (#24)
  myoe_diary    — 묘에 자기관찰 일지 (#16)
  learning_log  — Stickgold 72h 학습 로그 (#19)
"""

from engine.storage.db import (
    get_connection,
    init_db,
    new_user_id,
    DB_PATH,
)
from engine.storage.repositories import (
    UserRepo,
    DreamDiaryRepo,
    ClinicalLogRepo,
    IRTSessionRepo,
    MyoeDiaryRepo,
    LearningLogRepo,
)
from engine.storage.ops import (
    init_ops_tables,
    ErrorLogRepo,
    CrisisStatsRepo,
    RateLimitRepo,
    backup_db,
)

__all__ = [
    "get_connection",
    "init_db",
    "new_user_id",
    "DB_PATH",
    "UserRepo",
    "DreamDiaryRepo",
    "ClinicalLogRepo",
    "IRTSessionRepo",
    "MyoeDiaryRepo",
    "LearningLogRepo",
    "init_ops_tables",
    "ErrorLogRepo",
    "CrisisStatsRepo",
    "RateLimitRepo",
    "backup_db",
]
