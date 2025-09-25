"""대운/세운 분석기."""

from __future__ import annotations

from itertools import combinations

from saju_program import rules_data
from saju_program.saju_core import Pillar


class SajuFortuneAnalyzer:
    """원국과 운세 기둥을 비교하여 합·충·형·파·삼합 등을 탐지한다."""

    def __init__(self, saju, daewoon: Pillar, sewoon: Pillar):
        self.saju = saju
        self.daewoon = daewoon
        self.sewoon = sewoon

    def generate_report(self) -> str:
        lines: list[str] = ["--- 대운/세운 분석 ---"]
        lines.append(f"대운: {self.daewoon}")
        lines.extend(self._describe_fortune_interaction(self.daewoon, "대운"))
        lines.append("")
        lines.append(f"세운: {self.sewoon}")
        lines.extend(self._describe_fortune_interaction(self.sewoon, "세운"))
        samhap_lines = self._detect_samhap()
        if samhap_lines:
            lines.append("")
            lines.append("삼합·삼형성 체크")
            lines.extend(samhap_lines)
        lines.append("-" * 20)
        return "\n".join(lines)

    def _describe_fortune_interaction(self, fortune_pillar: Pillar, label: str) -> list[str]:
        results: list[str] = []
        natal_branches = [pillar.branch.name for pillar in self.saju.get_pillars()]
        natal_stems = [pillar.stem.name for pillar in self.saju.get_pillars()]

        branch_message = self._check_branch_relations(fortune_pillar.branch.name, natal_branches, label)
        if branch_message:
            results.extend(branch_message)
        stem_message = self._check_stem_presence(fortune_pillar.stem.name, natal_stems, label)
        if stem_message:
            results.append(stem_message)
        myogo_message = self._check_myogo(fortune_pillar.branch.name)
        if myogo_message:
            results.append(myogo_message)
        if not results:
            results.append("  - 특이 관계가 감지되지 않았습니다.")
        return results

    def _check_branch_relations(self, branch: str, natal_branches: list[str], label: str) -> list[str]:
        messages: list[str] = []
        for natal in natal_branches:
            pair = (branch, natal)
            if self._pair_contains(rules_data.CHONG, *pair):
                messages.append(f"  - {label} 지지 {branch} ↔ {natal}: 충(沖)으로 변동·이별 신호")
            elif self._pair_contains(rules_data.XING, *pair):
                messages.append(f"  - {label} 지지 {branch} ↔ {natal}: 형(刑)으로 갈등·법적 이슈")
            elif self._pair_contains(rules_data.PO, *pair):
                messages.append(f"  - {label} 지지 {branch} ↔ {natal}: 파(破)로 손실·균열 가능성")
            elif self._pair_contains(rules_data.CHUAN, *pair):
                messages.append(f"  - {label} 지지 {branch} ↔ {natal}: 천(穿)으로 강한 제압수단")
            elif self._pair_contains(rules_data.HAP, *pair):
                messages.append(f"  - {label} 지지 {branch} ↔ {natal}: 합(合)으로 협력·결속")
        return messages

    def _check_stem_presence(self, stem: str, natal_stems: list[str], label: str) -> str | None:
        if stem in natal_stems:
            return f"  - {label} 천간 {stem}: 원국과 동일하여 기질이 증폭됩니다."
        return None

    def _check_myogo(self, branch: str) -> str | None:
        if branch in rules_data.MYOGO_BRANCHES:
            return f"  - 지지 {branch}: 묘고(墓庫) 기운 활성화 가능, 형/충 여부를 확인하세요."
        return None

    def _detect_samhap(self) -> list[str]:
        branches = [pillar.branch.name for pillar in self.saju.get_pillars()]
        branches.extend([self.daewoon.branch.name, self.sewoon.branch.name])
        matches: list[str] = []
        for combo in combinations(branches, 3):
            for target, element in rules_data.SAMHAP.items():
                if set(combo) == set(target):
                    matches.append(
                        f"  - {'/'.join(combo)}: 삼합 완성 → {element.upper()} 기운 강화"
                    )
        return matches

    @staticmethod
    def _pair_contains(pair_set: set[tuple[str, str]], a: str, b: str) -> bool:
        return (a, b) in pair_set or (b, a) in pair_set
