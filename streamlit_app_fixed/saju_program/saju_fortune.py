"""대운/세운 분석 스켈레톤."""

from __future__ import annotations

from typing import List

from .saju_core import Pillar
from .saju_model import Saju


class SajuFortuneAnalyzer:
    """대운과 세운 상호작용을 담당하는 분석 클래스."""

    def __init__(self, saju: Saju, daewoon: Pillar, sewoon: Pillar) -> None:
        self.saju = saju
        self.daewoon = daewoon
        self.sewoon = sewoon

    def analyze_interactions(self) -> List[str]:
        """합/충/형/파/입묘 감지 로직을 추가하기 위한 기본 틀."""

        lines = ["--- 대운/세운 분석 ---"]
        lines.append(f"대운: {self.daewoon}")
        lines.append(f"세운: {self.sewoon}")
        lines.append("(TODO) 합·충·형·파·입묘 감지 로직을 추가하세요.")
        lines.append("-" * 20)
        return lines

    def print_report(self) -> None:
        for line in self.analyze_interactions():
            print(line)


__all__ = ["SajuFortuneAnalyzer"]

