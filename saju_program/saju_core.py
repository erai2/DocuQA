"""Core domain models for Saju analysis."""

from __future__ import annotations

class HeavenlyStem:
    """Represents one of the ten heavenly stems (천간)."""

    def __init__(self, name: str, ohaeng: str, yinyang: str) -> None:
        self.name = name
        self.ohaeng = ohaeng
        self.yinyang = yinyang

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}"


class EarthlyBranch:
    """Represents one of the twelve earthly branches (지지)."""

    def __init__(self, name: str, ohaeng: str, yinyang: str) -> None:
        self.name = name
        self.ohaeng = ohaeng
        self.yinyang = yinyang

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}"


class Gungwi:
    """Represents the palace/house (궁위) associated with each pillar."""

    def __init__(self, name: str, representative_kin: str, symbolic_meaning: str) -> None:
        self.name = name
        self.representative_kin = representative_kin
        self.symbolic_meaning = symbolic_meaning

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name}({self.representative_kin})"


class Pillar:
    """Represents one pillar consisting of a stem, branch, and optional 궁위."""

    def __init__(self, stem: HeavenlyStem, branch: EarthlyBranch, gungwi: Gungwi | None = None) -> None:
        self.stem = stem
        self.branch = branch
        self.gungwi = gungwi

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        if self.gungwi:
            return f"{self.stem}{self.branch}({self.gungwi.name})"
        return f"{self.stem}{self.branch}"


class GungwiManager:
    """Provides a simple lookup for 궁위 definitions."""

    def __init__(self) -> None:
        self.gungwi_map = {
            "년주": Gungwi("년주", "부모궁", "조상·가계·가문"),
            "월주": Gungwi("월주", "부모궁", "부모·형제·사회적 기반"),
            "일주": Gungwi("일주", "배우자궁", "자기 자신·배우자"),
            "시주": Gungwi("시주", "자식궁", "자녀·후손·말년"),
        }

    def get_gungwi(self, name: str) -> Gungwi | None:
        return self.gungwi_map.get(name)
