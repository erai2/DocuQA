"""Static rule tables used throughout the 사주 도구."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple

# --- 기본 데이터 ---------------------------------------------------------

HEAVENLY_STEMS: Dict[str, Dict[str, str]] = {
    "甲": {"ohaeng": "목", "yinyang": "양"},
    "乙": {"ohaeng": "목", "yinyang": "음"},
    "丙": {"ohaeng": "화", "yinyang": "양"},
    "丁": {"ohaeng": "화", "yinyang": "음"},
    "戊": {"ohaeng": "토", "yinyang": "양"},
    "己": {"ohaeng": "토", "yinyang": "음"},
    "庚": {"ohaeng": "금", "yinyang": "양"},
    "辛": {"ohaeng": "금", "yinyang": "음"},
    "壬": {"ohaeng": "수", "yinyang": "양"},
    "癸": {"ohaeng": "수", "yinyang": "음"},
}

EARTHLY_BRANCHES: Dict[str, Dict[str, object]] = {
    "子": {
        "ohaeng": "수",
        "yinyang": "양",
        "gijeong": {"임": {"ohaeng": "수", "yinyang": "양"}},
    },
    "丑": {
        "ohaeng": "토",
        "yinyang": "음",
        "gijeong": {
            "계": {"ohaeng": "수", "yinyang": "음"},
            "신": {"ohaeng": "금", "yinyang": "음"},
            "기": {"ohaeng": "토", "yinyang": "음"},
        },
    },
    "寅": {
        "ohaeng": "목",
        "yinyang": "양",
        "gijeong": {
            "무": {"ohaeng": "토", "yinyang": "양"},
            "병": {"ohaeng": "화", "yinyang": "양"},
            "갑": {"ohaeng": "목", "yinyang": "양"},
        },
    },
    "卯": {
        "ohaeng": "목",
        "yinyang": "음",
        "gijeong": {
            "갑": {"ohaeng": "목", "yinyang": "양"},
            "을": {"ohaeng": "목", "yinyang": "음"},
        },
    },
    "辰": {
        "ohaeng": "토",
        "yinyang": "양",
        "gijeong": {
            "을": {"ohaeng": "목", "yinyang": "음"},
            "계": {"ohaeng": "수", "yinyang": "음"},
            "무": {"ohaeng": "토", "yinyang": "양"},
        },
    },
    "巳": {
        "ohaeng": "화",
        "yinyang": "음",
        "gijeong": {
            "무": {"ohaeng": "토", "yinyang": "양"},
            "경": {"ohaeng": "금", "yinyang": "양"},
            "병": {"ohaeng": "화", "yinyang": "양"},
        },
    },
    "午": {
        "ohaeng": "화",
        "yinyang": "양",
        "gijeong": {
            "기": {"ohaeng": "토", "yinyang": "음"},
            "병": {"ohaeng": "화", "yinyang": "양"},
        },
    },
    "未": {
        "ohaeng": "토",
        "yinyang": "음",
        "gijeong": {
            "정": {"ohaeng": "화", "yinyang": "음"},
            "을": {"ohaeng": "목", "yinyang": "음"},
            "기": {"ohaeng": "토", "yinyang": "음"},
        },
    },
    "申": {
        "ohaeng": "금",
        "yinyang": "양",
        "gijeong": {
            "무": {"ohaeng": "토", "yinyang": "양"},
            "임": {"ohaeng": "수", "yinyang": "양"},
            "경": {"ohaeng": "금", "yinyang": "양"},
        },
    },
    "酉": {
        "ohaeng": "금",
        "yinyang": "음",
        "gijeong": {
            "경": {"ohaeng": "금", "yinyang": "양"},
            "신": {"ohaeng": "금", "yinyang": "음"},
        },
    },
    "戌": {
        "ohaeng": "토",
        "yinyang": "양",
        "gijeong": {
            "신": {"ohaeng": "금", "yinyang": "음"},
            "정": {"ohaeng": "화", "yinyang": "음"},
            "무": {"ohaeng": "토", "yinyang": "양"},
        },
    },
    "亥": {
        "ohaeng": "수",
        "yinyang": "음",
        "gijeong": {
            "무": {"ohaeng": "토", "yinyang": "양"},
            "갑": {"ohaeng": "목", "yinyang": "양"},
            "임": {"ohaeng": "수", "yinyang": "양"},
        },
    },
}

WUXING = {**{k: v["ohaeng"] for k, v in HEAVENLY_STEMS.items()}, **{k: v["ohaeng"] for k, v in EARTHLY_BRANCHES.items()}}

OHAENG_ORDER: Sequence[str] = ("목", "화", "토", "금", "수")


# --- 지지 상호작용 세트 -------------------------------------------------

CHONG = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")}
XING = {
    ("子", "卯"),
    ("丑", "戌"),
    ("寅", "巳"),
    ("卯", "子"),
    ("辰", "辰"),
    ("巳", "申"),
    ("午", "午"),
    ("未", "丑"),
    ("申", "巳"),
    ("酉", "酉"),
    ("戌", "丑"),
    ("亥", "亥"),
}
PO = {("子", "酉"), ("卯", "午"), ("寅", "亥"), ("辰", "丑"), ("巳", "申"), ("未", "戌")}
CHUAN = {("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")}
HAP = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}
SAMHAP = {
    ("寅", "午", "戌"): "화",
    ("巳", "酉", "丑"): "금",
    ("申", "子", "辰"): "수",
    ("亥", "卯", "未"): "목",
}


# --- 십신 판단을 위한 보조 데이터 ---------------------------------------

OHAENG_RELATIONS = {
    "목": {"생": "화", "극": "토", "피생": "수", "피극": "금"},
    "화": {"생": "토", "극": "금", "피생": "목", "피극": "수"},
    "토": {"생": "금", "극": "수", "피생": "화", "피극": "목"},
    "금": {"생": "수", "극": "목", "피생": "토", "피극": "화"},
    "수": {"생": "목", "극": "화", "피생": "금", "피극": "토"},
}

SIPSIN_MAP = {
    ("비슷", "음양같음"): "비견",
    ("비슷", "음양다름"): "겁재",
    ("생", "음양같음"): "식신",
    ("생", "음양다름"): "상관",
    ("피생", "음양같음"): "편인",
    ("피생", "음양다름"): "정인",
    ("극", "음양같음"): "편재",
    ("극", "음양다름"): "정재",
    ("피극", "음양같음"): "편관",
    ("피극", "음양다름"): "정관",
}

SHISHIN_DEFAULT_DATA = {
    "비견": {"description": "자아·주체성"},
    "겁재": {"description": "경쟁·독립심"},
    "식신": {"description": "재능·표현력"},
    "상관": {"description": "언변·임기응변"},
    "정재": {"description": "안정적 재물"},
    "편재": {"description": "유동 자금·사업"},
    "정관": {"description": "명예·규범"},
    "편관": {"description": "권력·통제"},
    "정인": {"description": "학문·문서"},
    "편인": {"description": "기획력·직관"},
}


# --- 유틸리티 -----------------------------------------------------------

def pair_contains(pair_set: Iterable[Tuple[str, str]], a: str, b: str) -> bool:
    """Return True if the unordered pair exists in ``pair_set``."""

    return (a, b) in pair_set or (b, a) in pair_set


def build_wuxing_lookup(values: Sequence[str]) -> Dict[str, List[str]]:
    """Group 천간/지지를 오행 기준으로 묶는다."""

    grouped: Dict[str, List[str]] = defaultdict(list)
    for symbol, ohaeng in values:
        grouped[ohaeng].append(symbol)
    return grouped


def has_root(stem_name: str, branches: Sequence[str]) -> bool:
    """Return True if ``stem_name`` finds 같은 오행 among ``branches``."""

    stem_ohaeng = WUXING.get(stem_name, "")
    return any(WUXING.get(branch, "") == stem_ohaeng for branch in branches)
