"""Core domain models and factories for Saju analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional


@dataclass(slots=True)
class HeavenlyStem:
    """Represents one of the ten heavenly stems (천간)."""

    name: str
    ohaeng: str
    yinyang: str
    sipsin: Optional[str] = None  # 십신은 동적으로 할당

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}"


@dataclass(slots=True)
class EarthlyBranch:
    """Represents one of the twelve earthly branches (지지)."""

    name: str
    ohaeng: str
    yinyang: str
    gijeong: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}"


@dataclass(slots=True)
class Gungwi:
    """Represents the palace/house (궁위) associated with each pillar."""

    name: str
    life_stage: str
    representative_kin: str
    symbolic_meaning: str

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}({self.representative_kin})"


@dataclass(slots=True)
class Shishin:
    """Describes one of the ten gods (십신) with optional relationship metadata."""

    name: str
    description: str
    relations: Dict[str, str] = field(default_factory=dict)

    def get_relationship(self, other_shishin_name: str) -> str:
        return self.relations.get(other_shishin_name, "관계 없음")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Shishin(name='{self.name}')"


@dataclass(slots=True)
class Pillar:
    """Represents one pillar consisting of a stem, branch, and optional 궁위."""

    stem: HeavenlyStem
    branch: EarthlyBranch
    gungwi: Optional[Gungwi] = None

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        if self.gungwi:
            return f"{self.stem}{self.branch}({self.gungwi.name})"
        return f"{self.stem}{self.branch}"


class GungwiManager:
    """Provides lookup access for 궁위 definitions."""

    def __init__(self, data: Optional[Dict[str, Dict[str, str]]] = None) -> None:
        if data is None:
            data = {
                "년주": {
                    "life_stage": "유년 시기 (1-18세)",
                    "representative_kin": "조상·부모·노인·선배",
                    "symbolic_meaning": "해외·원방·변방지역",
                },
                "월주": {
                    "life_stage": "청년 시기 (18-35세)",
                    "representative_kin": "부모·형제·동료·상사",
                    "symbolic_meaning": "본적·고향·일터",
                },
                "일주": {
                    "life_stage": "장년 시기 (35-55세)",
                    "representative_kin": "배우자·가까운 지인",
                    "symbolic_meaning": "자아·사유재산",
                },
                "시주": {
                    "life_stage": "말년 (55세 이후)",
                    "representative_kin": "자녀·후배·제자",
                    "symbolic_meaning": "문호·출구·미래",
                },
            }

        self._gungwis = {
            name: Gungwi(
                name=name,
                life_stage=info["life_stage"],
                representative_kin=info["representative_kin"],
                symbolic_meaning=info["symbolic_meaning"],
            )
            for name, info in data.items()
        }

    def get_gungwi(self, name: str) -> Optional[Gungwi]:
        return self._gungwis.get(name)


class ShishinManager:
    """Stores 십신 metadata referenced during 분석."""

    def __init__(self, data: Dict[str, Dict[str, str]]) -> None:
        self._shishins = {
            name: Shishin(
                name=name,
                description=info.get("description", ""),
                relations=info.get("relations", {}),
            )
            for name, info in data.items()
        }

    def get_shishin(self, name: str) -> Optional[Shishin]:
        return self._shishins.get(name)


def create_heavenly_stem(name: str) -> HeavenlyStem:
    """Factory that builds a :class:`HeavenlyStem` from rules data."""

    from . import rules_data

    data = rules_data.HEAVENLY_STEMS.get(name)
    if data is None:
        raise KeyError(f"알 수 없는 천간: {name}")
    return HeavenlyStem(name=name, ohaeng=data["ohaeng"], yinyang=data["yinyang"])


def create_earthly_branch(name: str) -> EarthlyBranch:
    """Factory that builds an :class:`EarthlyBranch` from rules data."""

    from . import rules_data

    data = rules_data.EARTHLY_BRANCHES.get(name)
    if data is None:
        raise KeyError(f"알 수 없는 지지: {name}")
    return EarthlyBranch(
        name=name,
        ohaeng=data["ohaeng"],
        yinyang=data["yinyang"],
        gijeong=data.get("gijeong", {}),
    )


def create_pillar(stem_name: str, branch_name: str, gungwi: Optional[Gungwi] = None) -> Pillar:
    """Convenience helper to construct a pillar from symbolic names."""

    return Pillar(create_heavenly_stem(stem_name), create_earthly_branch(branch_name), gungwi)


def assign_gungwi(pillars: Iterable[Pillar], gungwi_manager: GungwiManager) -> None:
    """Assign 궁위 information to the standard 년/월/일/시 pillar ordering."""

    order = ["년주", "월주", "일주", "시주"]
    for pillar, gungwi_name in zip(pillars, order):
        pillar.gungwi = gungwi_manager.get_gungwi(gungwi_name)
