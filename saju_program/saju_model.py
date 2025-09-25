"""Saju 모델과 궁위 분석기를 정의한다."""

from __future__ import annotations

from saju_program.saju_core import GungwiManager, Pillar


class Saju:
    """년·월·일·시주 네 기둥으로 구성된 사주 객체."""

    def __init__(self, year: Pillar, month: Pillar, day: Pillar, time: Pillar, gungwi_manager: GungwiManager):
        self.year = year
        self.month = month
        self.day = day
        self.time = time

        self.year.gungwi = gungwi_manager.get_gungwi("년주")
        self.month.gungwi = gungwi_manager.get_gungwi("월주")
        self.day.gungwi = gungwi_manager.get_gungwi("일주")
        self.time.gungwi = gungwi_manager.get_gungwi("시주")

    def get_pillars(self) -> list[Pillar]:
        return [self.year, self.month, self.day, self.time]

    def __repr__(self) -> str:
        return f"사주: {self.year}, {self.month}, {self.day}, {self.time}"


class SajuAnalyzer:
    """궁위 요약을 출력하는 기본 분석기."""

    def __init__(self, saju: Saju):
        self.saju = saju

    def analyze_gungwi(self) -> None:
        print("--- 궁위 분석 ---")
        for pillar in self.saju.get_pillars():
            if pillar.gungwi:
                print(f"{pillar}:")
                print(f"  - 대표 육친: {pillar.gungwi.representative_kin}")
                print(f"  - 상징 의미: {pillar.gungwi.symbolic_meaning}")
        print("-" * 20)
