"""Example script to demonstrate the saju program scaffolding."""

from __future__ import annotations

import os
import sys

if __package__ is None:  # pragma: no cover - script execution support
    PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(PACKAGE_ROOT))

from saju_program import (
    EarthlyBranch,
    GungwiManager,
    HeavenlyStem,
    Pillar,
    Saju,
    SajuAnalyzer,
    SajuFortuneAnalyzer,
)


def main() -> None:
    gungwi_manager = GungwiManager()

    # 예시 사주 (원국)
    sin = HeavenlyStem("辛", "금", "음")
    gi = HeavenlyStem("己", "토", "음")
    jeong = HeavenlyStem("丁", "화", "음")

    myo = EarthlyBranch("卯", "목", "음")
    chuk = EarthlyBranch("丑", "토", "음")
    yu = EarthlyBranch("酉", "금", "음")
    mi = EarthlyBranch("未", "토", "음")

    year_pillar = Pillar(jeong, mi)
    month_pillar = Pillar(gi, yu)
    day_pillar = Pillar(sin, chuk)
    time_pillar = Pillar(sin, myo)

    saju = Saju(year_pillar, month_pillar, day_pillar, time_pillar, gungwi_manager)
    print(saju)

    analyzer = SajuAnalyzer(saju)
    analyzer.analyze_gungwi()

    # 대운/세운 예시
    daewoon = Pillar(gi, yu)
    sewoon = Pillar(jeong, myo)
    fortune = SajuFortuneAnalyzer(saju, daewoon, sewoon)
    fortune.analyze_interactions()


if __name__ == "__main__":
    main()
