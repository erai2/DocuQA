"""예시 사주를 구성해 확장된 분석을 수행한다."""

from __future__ import annotations

import pathlib
import sys
from tempfile import TemporaryDirectory
from textwrap import dedent

if __package__ is None or __package__ == "":
    sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from saju_program import rules_data
from saju_program.saju_core import EarthlyBranch, GungwiManager, HeavenlyStem, Pillar, ShishinManager
from saju_program.saju_fortune import SajuFortuneAnalyzer
from saju_program.saju_model import Saju, SajuAnalyzer, parse_saju_documents


def _prepare_sample_docs(base: pathlib.Path) -> pathlib.Path:
    docs_dir = base / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample_md = docs_dir / "sample.md"
    sample_md.write_text(
        dedent(
            """
            # 사주 보조 규칙

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
    return docs_dir


def main() -> None:
    with TemporaryDirectory() as tmp:
        docs_dir = _prepare_sample_docs(pathlib.Path(tmp))
        parsed_data = parse_saju_documents(docs_dir)

        gungwi_manager = GungwiManager()
        shishin_manager = ShishinManager(rules_data.DEFAULT_SHISHIN_DATA)

        # 예시 사주 기둥 구성
        year_pillar = Pillar(HeavenlyStem.from_name("丙"), EarthlyBranch.from_name("申"))
        month_pillar = Pillar(HeavenlyStem.from_name("丙"), EarthlyBranch.from_name("申"))
        day_pillar = Pillar(HeavenlyStem.from_name("辛"), EarthlyBranch.from_name("酉"))
        time_pillar = Pillar(HeavenlyStem.from_name("丁"), EarthlyBranch.from_name("未"))

        saju = Saju(year_pillar, month_pillar, day_pillar, time_pillar, gungwi_manager)
        analyzer = SajuAnalyzer(saju, shishin_manager, parsed_data)
        report = analyzer.generate_report()
        print(report)

        daewoon = Pillar(HeavenlyStem.from_name("己"), EarthlyBranch.from_name("丑"))
        sewoon = Pillar(HeavenlyStem.from_name("丁"), EarthlyBranch.from_name("卯"))
        fortune = SajuFortuneAnalyzer(saju, daewoon, sewoon)
        print()
        print(fortune.generate_report())


if __name__ == "__main__":
    main()
