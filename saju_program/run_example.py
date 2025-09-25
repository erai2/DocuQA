"""Example script demonstrating the advanced 사주 분석 파이프라인."""

from __future__ import annotations

import os
import sys

if __package__ is None:  # pragma: no cover - script execution support
    PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(PACKAGE_ROOT))

from saju_program import (
    GungwiManager,
    Saju,
    SajuAnalyzer,
    SajuFortuneAnalyzer,
    create_pillar,
)


def main() -> None:
    gungwi_manager = GungwiManager()

    # 예시 사주 (丁丙辛戊 / 酉申酉未)
    year_pillar = create_pillar("丙", "申")
    month_pillar = create_pillar("丙", "申")
    day_pillar = create_pillar("辛", "酉")
    time_pillar = create_pillar("丁", "未")

    saju = Saju(year_pillar, month_pillar, day_pillar, time_pillar, gungwi_manager)
    print(saju)

    analyzer = SajuAnalyzer(saju)
    analyzer.analyze_gungwi()
    analyzer.analyze_sipsin()
    analyzer.analyze_branch_relations()
    analyzer.analyze_cheyong_and_jubin(ilgan_is_strong=False)
    analyzer.analyze_advanced_rules()
    analyzer.analyze_gongmang(["戌", "亥"])

    # 대운/세운 예시
    daewoon = create_pillar("己", "酉")
    sewoon = create_pillar("丁", "卯")
    fortune = SajuFortuneAnalyzer(saju, daewoon, sewoon)
    fortune.analyze_interactions()


if __name__ == "__main__":
    main()
