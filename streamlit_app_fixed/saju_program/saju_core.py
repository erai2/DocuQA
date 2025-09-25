"""Core domain objects for the 사주(四柱) 분석 모듈.

이 모듈은 천간과 지지, 그리고 이를 결합한 기둥(Pillar)을 표현하는 클래스를
제공한다. 또한 궁위(宮位) 개념을 다루는 ``Gungwi`` 및 ``GungwiManager`` 를
포함해 이후의 분석 로직이 쉽게 확장될 수 있도록 기본 토대를 마련한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(slots=True)
class HeavenlyStem:
    """천간(天干)을 표현한다."""

    name: str
    ohaeng: str
    yinyang: str

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return self.name


@dataclass(slots=True)
class EarthlyBranch:
    """지지(地支)를 표현한다."""

    name: str
    ohaeng: str
    yinyang: str

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return self.name


@dataclass(slots=True)
class Gungwi:
    """궁위 메타데이터를 담는다."""

    name: str
    representative_kin: str
    symbolic_meaning: str

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"{self.name}({self.representative_kin})"


@dataclass(slots=True)
class Pillar:
    """천간과 지지를 결합한 기둥(주柱)."""

    stem: HeavenlyStem
    branch: EarthlyBranch
    gungwi: Optional[Gungwi] = None

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        if self.gungwi:
            return f"{self.stem}{self.branch}({self.gungwi.name})"
        return f"{self.stem}{self.branch}"


class GungwiManager:
    """궁위 정보를 일괄 관리하는 헬퍼."""

    def __init__(self) -> None:
        self._gungwi_map: Dict[str, Gungwi] = {
            "년주": Gungwi("년주", "부모궁", "조상·가계·가문"),
            "월주": Gungwi("월주", "부모궁", "부모·형제·사회적 기반"),
            "일주": Gungwi("일주", "배우자궁", "자기 자신·배우자"),
            "시주": Gungwi("시주", "자식궁", "자녀·후손·말년"),
        }

    def get_gungwi(self, name: str) -> Optional[Gungwi]:
        """궁위 이름으로 ``Gungwi`` 객체를 조회한다."""

        return self._gungwi_map.get(name)


__all__ = [
    "EarthlyBranch",
    "Gungwi",
    "GungwiManager",
    "HeavenlyStem",
    "Pillar",
]

