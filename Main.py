"""Main pipeline orchestrating 문서 업로드 → 파싱 → 사주 객체화 → DB 저장."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from textwrap import dedent

from saju_program import rules_data
from saju_program.saju_core import EarthlyBranch, GungwiManager, HeavenlyStem, Pillar, ShishinManager
from saju_program.saju_fortune import SajuFortuneAnalyzer
from saju_program.saju_model import Saju, SajuAnalyzer, parse_saju_documents

UPLOAD_DIR = Path("uploads")
DB_PATH = Path("saju_reports.db")


def simulate_upload() -> Path:
    """샘플 문서를 업로드 디렉터리에 저장한다."""

    UPLOAD_DIR.mkdir(exist_ok=True)
    sample_file = UPLOAD_DIR / "guide.md"
    sample_file.write_text(
        dedent(
            """
            # 업로드된 사주 문서

            체: 비견, 겁재, 정인
            용: 정재, 편재, 정관
            중립: 식신, 상관

            공망 갑자: 갑자, 을축
            공망 병인: 경신, 신유

            묘고의 원칙
            • 묘고는 형/충을 기뻐하며, 형/충이 없으면 묘가 된다.

            허실 판단
            • 지지가 뿌리가 되지 못하면 허투로 본다.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return UPLOAD_DIR


def build_saju(parsed_data: dict[str, object]):
    """샘플 원국/대운/세운을 생성하고 분석 결과를 반환한다."""

    gungwi_manager = GungwiManager()
    shishin_manager = ShishinManager(rules_data.DEFAULT_SHISHIN_DATA)

    year_pillar = Pillar(HeavenlyStem.from_name("丙"), EarthlyBranch.from_name("申"))
    month_pillar = Pillar(HeavenlyStem.from_name("丙"), EarthlyBranch.from_name("申"))
    day_pillar = Pillar(HeavenlyStem.from_name("辛"), EarthlyBranch.from_name("酉"))
    time_pillar = Pillar(HeavenlyStem.from_name("丁"), EarthlyBranch.from_name("未"))

    saju = Saju(year_pillar, month_pillar, day_pillar, time_pillar, gungwi_manager)
    analyzer = SajuAnalyzer(saju, shishin_manager, parsed_data)
    natal_report = analyzer.generate_report()

    daewoon = Pillar(HeavenlyStem.from_name("己"), EarthlyBranch.from_name("丑"))
    sewoon = Pillar(HeavenlyStem.from_name("丁"), EarthlyBranch.from_name("卯"))
    fortune_analyzer = SajuFortuneAnalyzer(saju, daewoon, sewoon)
    fortune_report = fortune_analyzer.generate_report()

    metadata = {
        "natal": [f"{p.stem.name}{p.branch.name}" for p in saju.get_pillars()],
        "daewoon": f"{daewoon.stem.name}{daewoon.branch.name}",
        "sewoon": f"{sewoon.stem.name}{sewoon.branch.name}",
    }

    return natal_report, fortune_report, metadata


def store_reports(natal_report: str, fortune_report: str, metadata: dict[str, object]) -> None:
    """분석 결과를 SQLite 데이터베이스에 저장한다."""

    connection = sqlite3.connect(DB_PATH)
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                natal_report TEXT NOT NULL,
                fortune_report TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO reports(created_at, natal_report, fortune_report, metadata)
            VALUES(?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                natal_report,
                fortune_report,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    upload_path = simulate_upload()
    print(f"[1/4] 문서 업로드 완료: {upload_path.resolve()}")

    parsed_data = parse_saju_documents(upload_path)
    print(f"[2/4] 문서 파싱 완료: {', '.join(parsed_data.keys())}")

    print("[3/4] 사주 분석 실행...")
    natal_report, fortune_report, metadata = build_saju(parsed_data)
    print(natal_report)
    print()
    print(fortune_report)

    print("[4/4] 결과를 DB에 저장합니다...")
    store_reports(natal_report, fortune_report, metadata)
    print(f"[4/4] 저장 완료: {DB_PATH.resolve()}")


if __name__ == "__main__":
    main()

