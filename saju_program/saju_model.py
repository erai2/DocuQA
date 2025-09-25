"""Models and analyzers for the natal chart (원국) including 궁위 logic."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable, List, Optional, Sequence

from . import rules_data
from .saju_core import (
    GungwiManager,
    Pillar,
    ShishinManager,
    assign_gungwi,
)


class Saju:
    """Represents a natal chart consisting of four pillars."""

    def __init__(
        self,
        year: Pillar,
        month: Pillar,
        day: Pillar,
        time: Pillar,
        gungwi_manager: Optional[GungwiManager] = None,
    ) -> None:
        self.year = year
        self.month = month
        self.day = day
        self.time = time

        if gungwi_manager is None:
            gungwi_manager = GungwiManager()
        assign_gungwi(self.get_pillars(), gungwi_manager)

    def get_pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.time]

    def get_stems(self) -> List[str]:
        return [pillar.stem.name for pillar in self.get_pillars()]

    def get_branches(self) -> List[str]:
        return [pillar.branch.name for pillar in self.get_pillars()]

    def __iter__(self) -> Iterable[Pillar]:
        return iter(self.get_pillars())

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"사주: {self.year}, {self.month}, {self.day}, {self.time}"


class SajuAnalyzer:
    """고급 사주 분석 (궁위·십신·형충파해·묘고 등)을 수행합니다."""

    def __init__(self, saju: Saju, shishin_manager: Optional[ShishinManager] = None) -> None:
        self.saju = saju
        if shishin_manager is None:
            shishin_manager = ShishinManager(rules_data.SHISHIN_DEFAULT_DATA)
        self.shishin_manager = shishin_manager

    # --- 십신 계산 -----------------------------------------------------
    def calculate_sipsin(self, ilgan, target) -> str:
        if ilgan.name == target.name:
            return "일간"

        ilgan_ohaeng = ilgan.ohaeng
        target_ohaeng = target.ohaeng
        ohaeng_relation = "비슷"

        relation_map = rules_data.OHAENG_RELATIONS[ilgan_ohaeng]
        if relation_map["생"] == target_ohaeng:
            ohaeng_relation = "생"
        elif relation_map["극"] == target_ohaeng:
            ohaeng_relation = "극"
        elif relation_map["피생"] == target_ohaeng:
            ohaeng_relation = "피생"
        elif relation_map["피극"] == target_ohaeng:
            ohaeng_relation = "피극"

        yinyang_relation = "음양같음" if ilgan.yinyang == target.yinyang else "음양다름"
        return rules_data.SIPSIN_MAP.get((ohaeng_relation, yinyang_relation), "십신 계산 오류")

    def analyze_sipsin(self) -> None:
        print("--- 십신 분석 ---")
        ilgan = self.saju.day.stem
        branch_names = self.saju.get_branches()

        for pillar in self.saju:
            print(f"**{pillar}**")
            stem_sipsin_name = self.calculate_sipsin(ilgan, pillar.stem)
            if stem_sipsin_name == "일간":
                print(f"  > 천간: {pillar.stem.name} (일간)")
            else:
                print(f"  > 천간: {pillar.stem.name}는 {stem_sipsin_name}입니다.")
                has_root = rules_data.has_root(pillar.stem.name, branch_names)
                description = self.shishin_manager.get_shishin(stem_sipsin_name)
                if has_root:
                    print("    - 지지의 뿌리를 얻어 실(實)합니다.")
                else:
                    extra = f" ({description.description})" if description else ""
                    print(f"    - 지지에 뿌리가 없어 허투(虛透)합니다.{extra}")

            print("  > 지장간 십신:")
            for gan_name, gan_info in pillar.branch.gijeong.items():
                temp_stem = type(pillar.stem)(gan_name, gan_info["ohaeng"], gan_info["yinyang"])
                gijeong_sipsin_name = self.calculate_sipsin(ilgan, temp_stem)
                print(f"    - {gan_name}는 {gijeong_sipsin_name}입니다.")
            print("-" * 20)

    # --- 궁위 -----------------------------------------------------------
    def analyze_gungwi(self) -> None:
        print("--- 궁위 분석 ---")
        for pillar in self.saju:
            if pillar.gungwi:
                print(f"**{pillar}**")
                print(f"  - 궁위: {pillar.gungwi.name}")
                print(f"  - 해당 시기: {pillar.gungwi.life_stage}")
                print(f"  - 대표 육친: {pillar.gungwi.representative_kin}")
                print(f"  - 상징 의미: {pillar.gungwi.symbolic_meaning}")
        print("-" * 20)

    # --- 지지 상호작용 -------------------------------------------------
    def analyze_branch_relations(self) -> None:
        print("--- 지지 관계 분석 (합·충·형·파·천) ---")
        branches = self.saju.get_branches()
        relations_found = False

        for left, right in combinations(branches, 2):
            if rules_data.pair_contains(rules_data.CHONG, left, right):
                print(f"  - {left}/{right}: 충(沖) → 충돌·변화·분리")
                relations_found = True
            elif rules_data.pair_contains(rules_data.XING, left, right):
                print(f"  - {left}/{right}: 형(刑) → 갈등·법적 문제")
                relations_found = True
            elif rules_data.pair_contains(rules_data.CHUAN, left, right):
                print(f"  - {left}/{right}: 천(穿) → 강한 제압·살상력")
                relations_found = True
            elif rules_data.pair_contains(rules_data.PO, left, right):
                print(f"  - {left}/{right}: 파(破) → 균열·와해")
                relations_found = True
            elif rules_data.pair_contains(rules_data.HAP, left, right):
                print(f"  - {left}/{right}: 합(合) → 결합·협력")
                relations_found = True

        # 삼합 체크
        for combo, element in rules_data.SAMHAP.items():
            if all(branch in branches for branch in combo):
                joined = "/".join(combo)
                print(f"  - {joined}: 삼합으로 {element} 기운이 강화됩니다.")
                relations_found = True

        if not relations_found:
            print("  - 사주에 특이한 지지 관계가 없습니다.")
        print("-" * 20)

    # --- 체용 및 주빈 ---------------------------------------------------
    def analyze_cheyong_and_jubin(self, ilgan_is_strong: bool = False) -> None:
        print("--- 체용(體用) 및 주빈(主賓) 분석 ---")
        ilgan_name = self.saju.day.stem.name
        print(f"일간 {ilgan_name} 기준으로 체/용을 판별합니다.")

        for pillar in self.saju:
            stem_sipsin = self.calculate_sipsin(self.saju.day.stem, pillar.stem)
            if stem_sipsin in {"식신", "상관"}:
                cheyong_type = "용" if ilgan_is_strong else "체"
            elif stem_sipsin in {"비견", "겁재", "정인", "편인"}:
                cheyong_type = "체"
            else:
                cheyong_type = "용"
            print(f"  - {pillar.stem.name}: {cheyong_type} ({stem_sipsin})")

        print("주위(主位): 일간·일주·시주")
        print("빈위(賓位): 년주·월주 및 외부 운")
        print("-" * 20)

    # --- 허실·묘고 ------------------------------------------------------
    def analyze_advanced_rules(self) -> None:
        print("--- 간지 허실 및 묘고 분석 ---")
        branch_list = self.saju.get_branches()

        print("[간지 허실]")
        for pillar in self.saju:
            stem_name = pillar.stem.name
            branch_name = pillar.branch.name
            same_element = rules_data.WUXING.get(stem_name) == rules_data.WUXING.get(branch_name)
            rooted_elsewhere = rules_data.has_root(stem_name, branch_list)
            is_heo = not (same_element or rooted_elsewhere)
            status = "실(實)" if not is_heo else "허(虛)"
            print(f"  - {stem_name}{branch_name}주: {status}한 기세")

        print("[묘고 상태]")
        myogo_branches = {"辰", "戌", "丑", "未"}
        for branch in branch_list:
            if branch in myogo_branches:
                has_interaction = any(
                    branch != other
                    and (
                        rules_data.pair_contains(rules_data.CHONG, branch, other)
                        or rules_data.pair_contains(rules_data.XING, branch, other)
                    )
                    for other in branch_list
                )
                status = "庫(고) → 활용 가능" if has_interaction else "墓(묘) → 잠재·정체"
                print(f"  - {branch}: {status}")
        print("-" * 20)

    # --- 공망 ------------------------------------------------------------
    def analyze_gongmang(self, gongmang_list: Sequence[str]) -> None:
        print("--- 공망(空亡) 체크 ---")
        matched = [symbol for symbol in gongmang_list if symbol in self.saju.get_stems() or symbol in self.saju.get_branches()]
        if matched:
            joined = ", ".join(matched)
            print(f"사주에 공망 기운 {joined} 이/가 포함됩니다 → 허무·손실·유명무실 경향")
        else:
            print("공망 기운이 포함되지 않았습니다.")
        print("-" * 20)
