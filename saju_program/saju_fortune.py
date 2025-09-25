"""대운/세운 분석기 기본 구조."""

from __future__ import annotations

from saju_program.saju_core import Pillar


class SajuFortuneAnalyzer:
    """원국과 운세 기둥을 보관하고 상호작용 분석을 준비한다."""

    def __init__(self, saju, daewoon: Pillar, sewoon: Pillar):
        self.saju = saju
        self.daewoon = daewoon
        self.sewoon = sewoon

    def analyze_interactions(self) -> None:
        print("--- 대운/세운 분석 ---")
        print(f"대운: {self.daewoon}")
        print(f"세운: {self.sewoon}")
        print("  (합/충/형/파/입묘 자동 감지는 추후 확장 예정)")
        print("-" * 20)
