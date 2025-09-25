"""Saju 모델, 문서 파서, 그리고 종합 분석기를 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from saju_program import rules_data
from saju_program.saju_core import (
    EarthlyBranch,
    GungwiManager,
    HeavenlyStem,
    Pillar,
    ShishinManager,
)


def parse_saju_documents(folder_path: str | Path) -> dict[str, object]:
    """Parse markdown/txt 문서를 스캔하여 분석 보조 데이터를 수집한다."""

    path = Path(folder_path)
    parsed = {
        "myogo_rules": {},
        "heosil_rules": {},
        "cheyong_sipsin": {},
        "gongmang": {},
    }
    if not path.exists():
        return parsed

    for file in path.iterdir():
        if file.suffix.lower() not in {".md", ".txt"}:
            continue
        content = file.read_text(encoding="utf-8")
        parsed["myogo_rules"][file.name] = _parse_bullets(content, r"묘고[\s\S]*?\n(.*?)\n\n")
        parsed["heosil_rules"][file.name] = _parse_bullets(content, r"허실[\s\S]*?\n(.*?)\n\n")
        parsed["cheyong_sipsin"].update(_parse_cheyong(content))
        parsed["gongmang"].update(_parse_gongmang(content))
    return parsed


def _parse_bullets(content: str, pattern: str) -> list[str]:
    block = re.search(pattern, content)
    if not block:
        return []
    return [line.strip("• ●-* ") for line in block.group(1).splitlines() if line.strip()]


def _parse_cheyong(content: str) -> dict[str, list[str]]:
    match = re.search(r"체\s*:?\s*(.*?)\n용\s*:?\s*(.*?)\n중립\s*:?\s*(.*?)\n", content)
    if not match:
        return {}
    return {
        "체": [s.strip() for s in match.group(1).split(',') if s.strip()],
        "용": [s.strip() for s in match.group(2).split(',') if s.strip()],
        "중립": [s.strip() for s in match.group(3).split(',') if s.strip()],
    }


def _parse_gongmang(content: str) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    for line in content.splitlines():
        if "공망" not in line:
            continue
        parts = re.split(r"[:：]", line, maxsplit=1)
        if len(parts) != 2:
            continue
        key = parts[0].replace("공망", "").strip()
        targets = [item.strip() for item in parts[1].split(',') if item.strip()]
        if key:
            results[key] = targets
    return results


@dataclass
class Saju:
    """년·월·일·시주 네 기둥으로 구성된 사주 객체."""

    year: Pillar
    month: Pillar
    day: Pillar
    time: Pillar

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

    def get_stems(self) -> list[HeavenlyStem]:
        return [pillar.stem for pillar in self.get_pillars()]

    def get_branches(self) -> list[EarthlyBranch]:
        return [pillar.branch for pillar in self.get_pillars()]

    def __repr__(self) -> str:  # pragma: no cover - formatting helper
        return f"사주: {self.year}, {self.month}, {self.day}, {self.time}"


class SajuAnalyzer:
    """궁위·십신·지지관계·묘고 등을 종합 분석한다."""

    def __init__(self, saju: Saju, shishin_manager: ShishinManager, parsed_data: dict[str, object] | None = None):
        self.saju = saju
        self.shishin_manager = shishin_manager
        self.parsed_data = parsed_data or {}

    def generate_report(self) -> str:
        sections = [
            self._render_gungwi_section(),
            self._render_sipsin_section(),
            self._render_branch_relations_section(),
            self._render_cheyong_section(),
            self._render_advanced_rules_section(),
            self._render_gongmang_section(),
        ]
        return "\n\n".join(section for section in sections if section)

    # --- 궁위 분석 ---------------------------------------------------------
    def _render_gungwi_section(self) -> str:
        lines = ["--- 궁위 분석 ---"]
        for pillar in self.saju.get_pillars():
            if not pillar.gungwi:
                continue
            lines.append(f"{pillar} : {pillar.gungwi.life_stage}")
            lines.append(f"  - 대표 육친: {pillar.gungwi.representative_kin}")
            lines.append(f"  - 상징 의미: {pillar.gungwi.symbolic_meaning}")
        lines.append("-" * 20)
        return "\n".join(lines)

    # --- 십신 분석 ---------------------------------------------------------
    def _render_sipsin_section(self) -> str:
        lines = ["--- 십신 분석 ---"]
        ilgan = self.saju.day.stem
        for pillar in self.saju.get_pillars():
            sipsin_name = self._calculate_sipsin(ilgan, pillar.stem)
            shishin = self.shishin_manager.get_shishin(sipsin_name)
            descriptor = shishin.description if shishin else "정의되지 않음"
            if pillar.stem.name == ilgan.name:
                lines.append(f"{pillar}: 일간")
            else:
                lines.append(f"{pillar}: {sipsin_name} ({descriptor})")
            if pillar.has_root():
                lines.append("  - 지지에 뿌리가 있어 실(實)함")
            else:
                lines.append("  - 지지에 뿌리가 없어 허투(虛透)")
            if pillar.branch.gijeong:
                for name, info in pillar.branch.gijeong.items():
                    hidden = HeavenlyStem(name, info["ohaeng"], info["yinyang"])
                    hidden_sipsin = self._calculate_sipsin(ilgan, hidden)
                    lines.append(f"    · 지장간 {name}: {hidden_sipsin}")
        lines.append("-" * 20)
        return "\n".join(lines)

    def _calculate_sipsin(self, ilgan: HeavenlyStem, target: HeavenlyStem) -> str:
        if ilgan.name == target.name:
            return "일간"
        relation = "비슷"
        ilgan_rel = rules_data.WUXING_RELATIONS[ilgan.ohaeng]
        if ilgan_rel["생"] == target.ohaeng:
            relation = "생"
        elif ilgan_rel["극"] == target.ohaeng:
            relation = "극"
        elif ilgan_rel["피생"] == target.ohaeng:
            relation = "피생"
        elif ilgan_rel["피극"] == target.ohaeng:
            relation = "피극"
        yin_relation = "음양같음" if ilgan.yinyang == target.yinyang else "음양다름"
        return rules_data.SIPSIN_MAP.get((relation, yin_relation), "미분류")

    # --- 지지 관계 ---------------------------------------------------------
    def _render_branch_relations_section(self) -> str:
        lines = ["--- 지지 합·충·형·파·천 ---"]
        branch_names = [branch.name for branch in self.saju.get_branches()]
        relations_found = False
        for i, first in enumerate(branch_names):
            for second in branch_names[i + 1 :]:
                relation = self._branch_relation(first, second)
                if relation:
                    lines.append(f"  - {first} ↔ {second}: {relation}")
                    relations_found = True
        if not relations_found:
            lines.append("  - 특별한 지지 관계가 없습니다.")
        lines.append("-" * 20)
        return "\n".join(lines)

    def _branch_relation(self, a: str, b: str) -> str | None:
        if self._pair_contains(rules_data.CHONG, a, b):
            return "충(沖): 충돌·변화"
        if self._pair_contains(rules_data.XING, a, b):
            return "형(刑): 갈등·압박"
        if self._pair_contains(rules_data.PO, a, b):
            return "파(破): 균열·손실"
        if self._pair_contains(rules_data.CHUAN, a, b):
            return "천(穿): 강한 제압수단"
        if self._pair_contains(rules_data.HAP, a, b):
            return "합(合): 결속·협력"
        return None

    # --- 체용 및 주빈 ------------------------------------------------------
    def _render_cheyong_section(self) -> str:
        lines = ["--- 체용/주빈 분석 ---"]
        ilgan = self.saju.day.stem
        cheyong_map = self.parsed_data.get("cheyong_sipsin") or rules_data.CHEYONG_GROUPS
        for pillar in self.saju.get_pillars():
            sipsin = self._calculate_sipsin(ilgan, pillar.stem)
            category = self._resolve_cheyong_category(sipsin, cheyong_map)
            lines.append(f"{pillar.stem.name}: {sipsin} → {category}")
        lines.append("")
        lines.append("주위(主位): 일간·일주·시주")
        lines.append("빈위(賓位): 년주·월주")
        lines.append("-" * 20)
        return "\n".join(lines)

    def _resolve_cheyong_category(self, sipsin: str, cheyong_map: dict[str, Iterable[str]]) -> str:
        for category, values in cheyong_map.items():
            if sipsin in values:
                return category
        return "중립"

    # --- 허실·묘고 등 ------------------------------------------------------
    def _render_advanced_rules_section(self) -> str:
        lines = ["--- 허실·묘고 분석 ---"]
        for pillar in self.saju.get_pillars():
            status = "실(實)" if pillar.has_root() else "허(虛)"
            lines.append(f"{pillar}: {status} 상태")
        myogo_lines = self._detect_myogo()
        if myogo_lines:
            lines.extend(myogo_lines)
        else:
            lines.append("묘고 지지가 없습니다.")
        lines.append("-" * 20)
        return "\n".join(lines)

    def _detect_myogo(self) -> list[str]:
        results: list[str] = []
        branch_names = [branch.name for branch in self.saju.get_branches()]
        for branch in branch_names:
            if branch not in rules_data.MYOGO_BRANCHES:
                continue
            interaction = any(
                self._pair_contains(rules_data.CHONG, branch, other)
                or self._pair_contains(rules_data.XING, branch, other)
                for other in branch_names
                if other != branch
            )
            state = "庫(고)로 작동" if interaction else "墓(묘)로 잠김"
            results.append(f"  - {branch}: 묘고 지지 → {state}")
        return results

    # --- 공망 분석 ---------------------------------------------------------
    def _render_gongmang_section(self) -> str:
        lines = ["--- 공망 분석 ---"]
        gongmang_map: dict[str, list[str]] = self.parsed_data.get("gongmang", {})  # type: ignore[arg-type]
        if not gongmang_map:
            lines.append("공망 정보가 제공되지 않았습니다.")
        else:
            pillars = self.saju.get_pillars()
            all_names = [p.stem.name + p.branch.name for p in pillars]
            for key, empties in gongmang_map.items():
                hits = [name for name in all_names if name in empties]
                if hits:
                    lines.append(f"  - {key}: 사주에 {', '.join(hits)} 공망 발생")
                else:
                    lines.append(f"  - {key}: 해당 공망 없음")
        lines.append("-" * 20)
        return "\n".join(lines)

    @staticmethod
    def _pair_contains(pair_set: set[tuple[str, str]], a: str, b: str) -> bool:
        return (a, b) in pair_set or (b, a) in pair_set
