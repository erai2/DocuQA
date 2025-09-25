"""Models and analyzers for the natal chart (원국) including 궁위 logic."""

from __future__ import annotations

from typing import Iterable, List

from .saju_core import GungwiManager, Pillar


class Saju:
    """Represents a natal chart consisting of four pillars."""

    def __init__(self, year: Pillar, month: Pillar, day: Pillar, time: Pillar, gungwi_manager: GungwiManager) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.time = time

        self.year.gungwi = gungwi_manager.get_gungwi("년주")
        self.month.gungwi = gungwi_manager.get_gungwi("월주")
        self.day.gungwi = gungwi_manager.get_gungwi("일주")
        self.time.gungwi = gungwi_manager.get_gungwi("시주")

    def get_pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.time]

    def __iter__(self) -> Iterable[Pillar]:
        return iter(self.get_pillars())

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"사주: {self.year}, {self.month}, {self.day}, {self.time}"


class SajuAnalyzer:
    """Performs basic 궁위-based analysis on the natal chart."""

    def __init__(self, saju: Saju) -> None:
        self.saju = saju

    def analyze_gungwi(self) -> None:
        print("--- 궁위 분석 ---")
        for pillar in self.saju:
            if pillar.gungwi:
                print(f"{pillar}:")
                print(f"  - 대표 육친: {pillar.gungwi.representative_kin}")
                print(f"  - 상징 의미: {pillar.gungwi.symbolic_meaning}")
        print("-" * 20)
