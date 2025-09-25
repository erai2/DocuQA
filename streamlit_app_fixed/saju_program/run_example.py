"""간단한 실행 예시.

``python -m streamlit_app_fixed.saju_program.run_example`` 로 실행하면 예시
원국에 대한 궁위 분석과 대운/세운 요약을 콘솔로 출력한다.
"""

from __future__ import annotations

from .saju_core import EarthlyBranch, GungwiManager, HeavenlyStem, Pillar
from .saju_fortune import SajuFortuneAnalyzer
from .saju_model import Saju, SajuAnalyzer


def build_example() -> None:
    gungwi_manager = GungwiManager()

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

    analyzer = SajuAnalyzer(saju)
    for line in analyzer.analyze_gungwi():
        print(line)

    daewoon = Pillar(gi, yu)
    sewoon = Pillar(jeong, myo)
    fortune = SajuFortuneAnalyzer(saju, daewoon, sewoon)
    for line in fortune.analyze_interactions():
        print(line)


if __name__ == "__main__":
    build_example()

