"""Core classes for Saju pillars, stems, branches, 궁위, and 십신."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from saju_program import rules_data


@dataclass(frozen=True, slots=True)
class HeavenlyStem:
    """Represents a single 천간 with its 오행과 음양 정보."""

    name: str
    ohaeng: str
    yinyang: str

    @classmethod
    def from_name(cls, name: str) -> "HeavenlyStem":
        try:
            data = rules_data.HEAVENLY_STEMS[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"알 수 없는 천간: {name}") from exc
        return cls(name=name, ohaeng=data["ohaeng"], yinyang=data["yinyang"])

    def __repr__(self) -> str:  # pragma: no cover - string formatting helper
        return f"{self.name}"


@dataclass(frozen=True, slots=True)
class EarthlyBranch:
    """Represents a single 지지 with 오행, 음양 및 지장간 정보."""

    name: str
    ohaeng: str
    yinyang: str
    gijeong: dict[str, dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_name(cls, name: str) -> "EarthlyBranch":
        try:
            data = rules_data.EARTHLY_BRANCHES[name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"알 수 없는 지지: {name}") from exc
        return cls(
            name=name,
            ohaeng=data["ohaeng"],
            yinyang=data["yinyang"],
            gijeong=data.get("gijeong", {}),
        )

    def __repr__(self) -> str:  # pragma: no cover - string formatting helper
        return f"{self.name}"


@dataclass(frozen=True, slots=True)
class Gungwi:
    """궁위(宮位)에 대한 이름, 대표 육친, 상징 의미를 관리한다."""

    name: str
    representative_kin: str
    symbolic_meaning: str
    life_stage: str | None = None

    def __repr__(self) -> str:  # pragma: no cover - string formatting helper
        return f"{self.name}({self.representative_kin})"


@dataclass(slots=True)
class Pillar:
    """천간과 지지, 선택적으로 궁위를 포함한 한 기둥."""

    stem: HeavenlyStem
    branch: EarthlyBranch
    gungwi: Gungwi | None = None

    def __repr__(self) -> str:  # pragma: no cover - formatting helper
        if self.gungwi:
            return f"{self.stem}{self.branch}({self.gungwi.name})"
        return f"{self.stem}{self.branch}"

    @property
    def hidden_stem_names(self) -> list[str]:
        """Return the list of 지장간 names for this pillar's 지지."""

        return list(self.branch.gijeong.keys())

    def has_root(self) -> bool:
        """Check if the pillar's stem has a root within the branch's 지장간."""

        for hidden in self.branch.gijeong.values():
            if hidden["ohaeng"] == self.stem.ohaeng:
                return True
        return False


class GungwiManager:
    """년·월·일·시주 궁위를 기본 매핑과 함께 제공한다."""

    def __init__(self, custom_data: dict[str, dict[str, str]] | None = None):
        source = custom_data or rules_data.DEFAULT_GUNGWI_DATA
        self.gungwi_map: dict[str, Gungwi] = {
            name: Gungwi(
                name=name,
                representative_kin=info["representative_kin"],
                symbolic_meaning=info["symbolic_meaning"],
                life_stage=info.get("life_stage"),
            )
            for name, info in source.items()
        }

    def get_gungwi(self, name: str) -> Gungwi | None:
        return self.gungwi_map.get(name)


@dataclass(frozen=True, slots=True)
class Shishin:
    """십신 단일 항목. 설명과 십신 간 관계를 포함한다."""

    name: str
    description: str
    relations: dict[str, str] = field(default_factory=dict)

    def relation_to(self, other: str) -> str:
        return self.relations.get(other, "관계 없음")


class ShishinManager:
    """십신 데이터를 이름으로 조회하는 간단한 컨테이너."""

    def __init__(self, data: dict[str, dict[str, object]] | None = None):
        raw = data or rules_data.DEFAULT_SHISHIN_DATA
        self._shishins = {
            name: Shishin(
                name=name,
                description=info.get("description", ""),
                relations=info.get("relations", {}),
            )
            for name, info in raw.items()
        }

    def get_shishin(self, name: str) -> Shishin | None:
        return self._shishins.get(name)

    def known(self) -> Iterable[str]:  # pragma: no cover - convenience
        return self._shishins.keys()
