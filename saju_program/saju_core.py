"""Core classes for Saju pillars, stems, branches, and 궁위 metadata."""


class HeavenlyStem:
    """Represents a single 천간 with its 오행과 음양 정보."""

    def __init__(self, name: str, ohaeng: str, yinyang: str):
        self.name = name
        self.ohaeng = ohaeng
        self.yinyang = yinyang

    def __repr__(self) -> str:
        return f"{self.name}"


class EarthlyBranch:
    """Represents a single 지지 with 오행과 음양 정보."""

    def __init__(self, name: str, ohaeng: str, yinyang: str):
        self.name = name
        self.ohaeng = ohaeng
        self.yinyang = yinyang

    def __repr__(self) -> str:
        return f"{self.name}"


class Gungwi:
    """궁위(宮位)에 대한 이름, 대표 육친, 상징 의미를 관리한다."""

    def __init__(self, name: str, representative_kin: str, symbolic_meaning: str):
        self.name = name
        self.representative_kin = representative_kin
        self.symbolic_meaning = symbolic_meaning

    def __repr__(self) -> str:
        return f"{self.name}({self.representative_kin})"


class Pillar:
    """천간과 지지, 선택적으로 궁위를 포함한 한 기둥."""

    def __init__(self, stem: HeavenlyStem, branch: EarthlyBranch, gungwi: Gungwi | None = None):
        self.stem = stem
        self.branch = branch
        self.gungwi = gungwi

    def __repr__(self) -> str:
        if self.gungwi:
            return f"{self.stem}{self.branch}({self.gungwi.name})"
        return f"{self.stem}{self.branch}"


class GungwiManager:
    """년·월·일·시주 궁위를 기본 매핑과 함께 제공한다."""

    def __init__(self):
        self.gungwi_map = {
            "년주": Gungwi("년주", "부모궁", "조상·가계·가문"),
            "월주": Gungwi("월주", "부모궁", "부모·형제·사회적 기반"),
            "일주": Gungwi("일주", "배우자궁", "자기 자신·배우자"),
            "시주": Gungwi("시주", "자식궁", "자녀·후손·말년"),
        }

    def get_gungwi(self, name: str) -> Gungwi | None:
        return self.gungwi_map.get(name)


class Shishin:
    """십신 단일 항목. 현재는 설명 필드만 포함한다."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return f"Shishin({self.name})"


class ShishinManager:
    """십신 데이터를 이름으로 조회하는 간단한 컨테이너."""

    def __init__(self, data: dict[str, dict[str, str]]):
        self._shishins = {name: Shishin(name, info.get("description", "")) for name, info in data.items()}

    def get_shishin(self, name: str) -> Shishin | None:
        return self._shishins.get(name)
