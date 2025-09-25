"""예시 사주를 구성해 기본 분석을 수행한다."""

from __future__ import annotations

import pathlib
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))

from saju_program.saju_core import EarthlyBranch, GungwiManager, HeavenlyStem, Pillar
from saju_program.saju_fortune import SajuFortuneAnalyzer
from saju_program.saju_model import Saju, SajuAnalyzer


def main() -> None:
    gungwi_manager = GungwiManager()

    # 예시 사주 기둥 구성
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

    daewoon = Pillar(gi, yu)
    sewoon = Pillar(jeong, myo)
    fortune = SajuFortuneAnalyzer(saju, daewoon, sewoon)
    fortune.analyze_interactions()


if __name__ == "__main__":
    main()
