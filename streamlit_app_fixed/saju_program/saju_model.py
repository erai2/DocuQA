"""사주 원국 및 기본 분석 로직."""

from __future__ import annotations

from typing import Iterable, List

from .saju_core import GungwiManager, Pillar


class Saju:
    """연월일시 네 기둥을 보관한다."""

    def __init__(
        self,
        year: Pillar,
        month: Pillar,
        day: Pillar,
        time: Pillar,
        gungwi_manager: GungwiManager,
    ) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.time = time

        # 궁위 정보 주입
        self.year.gungwi = gungwi_manager.get_gungwi("년주")
        self.month.gungwi = gungwi_manager.get_gungwi("월주")
        self.day.gungwi = gungwi_manager.get_gungwi("일주")
        self.time.gungwi = gungwi_manager.get_gungwi("시주")

    def get_pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.time]

    def __iter__(self) -> Iterable[Pillar]:  # pragma: no cover - trivial
        return iter(self.get_pillars())

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        joined = ", ".join(str(pillar) for pillar in self.get_pillars())
        return f"사주: {joined}"


class SajuAnalyzer:
    """궁위 설명을 출력하는 1차 분석기."""

    def __init__(self, saju: Saju) -> None:
        self.saju = saju

    def analyze_gungwi(self) -> List[str]:
        """궁위 분석 결과를 문자열 목록으로 반환한다."""

        results: List[str] = ["--- 궁위 분석 ---"]
        for pillar in self.saju.get_pillars():
            if pillar.gungwi is None:
                continue
            results.append(str(pillar))
            results.append(f"  - 대표 육친: {pillar.gungwi.representative_kin}")
            results.append(f"  - 상징 의미: {pillar.gungwi.symbolic_meaning}")
        results.append("-" * 20)
        return results

    def print_gungwi_report(self) -> None:
        """``analyze_gungwi`` 결과를 바로 출력한다."""

        for line in self.analyze_gungwi():
            print(line)


__all__ = ["Saju", "SajuAnalyzer"]

