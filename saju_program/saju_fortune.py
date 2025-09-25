"""Fortune analysis (대운/세운) interactions and detection logic."""

from __future__ import annotations

from itertools import combinations
from typing import List, Tuple

from . import rules_data
from .saju_core import Pillar
from .saju_model import Saju


class SajuFortuneAnalyzer:
    """대운·세운과 원국 간의 합·충·형·파·입묘를 감지합니다."""

    def __init__(self, saju: Saju, daewoon: Pillar, sewoon: Pillar) -> None:
        self.saju = saju
        self.daewoon = daewoon
        self.sewoon = sewoon

    def _collect_branch_sources(self) -> List[Tuple[str, str]]:
        return [
            ("원국-년", self.saju.year.branch.name),
            ("원국-월", self.saju.month.branch.name),
            ("원국-일", self.saju.day.branch.name),
            ("원국-시", self.saju.time.branch.name),
            ("대운", self.daewoon.branch.name),
            ("세운", self.sewoon.branch.name),
        ]

    def analyze_interactions(self) -> None:
        print("--- 대운/세운 합·충·형·파·입묘 분석 ---")
        print(f"대운: {self.daewoon}")
        print(f"세운: {self.sewoon}")

        branch_sources = self._collect_branch_sources()
        self._report_pairwise_relations(branch_sources)
        self._report_samhap(branch_sources)
        self._report_myogo(branch_sources)
        print("-" * 20)

    # ------------------------------------------------------------------
    def _report_pairwise_relations(self, branch_sources: List[Tuple[str, str]]) -> None:
        seen = False
        for (label_a, branch_a), (label_b, branch_b) in combinations(branch_sources, 2):
            relation = None
            message = ""
            if rules_data.pair_contains(rules_data.CHONG, branch_a, branch_b):
                relation = "충(沖)"
                message = "→ 충돌·변화·분리"
            elif rules_data.pair_contains(rules_data.XING, branch_a, branch_b):
                relation = "형(刑)"
                message = "→ 갈등·법적 이슈"
            elif rules_data.pair_contains(rules_data.PO, branch_a, branch_b):
                relation = "파(破)"
                message = "→ 균열·와해"
            elif rules_data.pair_contains(rules_data.CHUAN, branch_a, branch_b):
                relation = "천(穿)"
                message = "→ 강력한 제압"
            elif rules_data.pair_contains(rules_data.HAP, branch_a, branch_b):
                relation = "합(合)"
                message = "→ 결합·협력"

            if relation:
                print(f"  - {label_a}({branch_a}) ↔ {label_b}({branch_b}): {relation} {message}")
                seen = True

        if not seen:
            print("  - 운과 원국 사이에 특이 관계가 발견되지 않았습니다.")

    def _report_samhap(self, branch_sources: List[Tuple[str, str]]) -> None:
        available = {branch for _, branch in branch_sources}
        for combo, element in rules_data.SAMHAP.items():
            if all(branch in available for branch in combo):
                labels = [label for label, branch in branch_sources if branch in combo]
                joined_labels = "/".join(labels)
                joined_branches = "/".join(combo)
                print(f"  - {joined_branches} 삼합 성립 ({joined_labels}) → {element} 기운 극대화")

    def _report_myogo(self, branch_sources: List[Tuple[str, str]]) -> None:
        myogo_branches = {"辰", "戌", "丑", "未"}
        branch_map = {branch: label for label, branch in branch_sources}
        for branch in myogo_branches & set(branch_map.keys()):
            interacts = any(
                rules_data.pair_contains(rules_data.CHONG, branch, other)
                or rules_data.pair_contains(rules_data.XING, branch, other)
                for other in branch_map
                if other != branch
            )
            state = "입묘 → 庫(고)로 활용" if interacts else "입묘 → 墓(묘)로 정체"
            print(f"  - {branch_map[branch]}({branch}): {state}")
