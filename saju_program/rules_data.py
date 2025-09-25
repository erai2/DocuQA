"""사주 분석에 사용되는 기본 규칙 데이터."""

from __future__ import annotations

ohaeng_order = ["목", "화", "토", "금", "수"]

# --- 천간/지지 기본 데이터 -------------------------------------------------

HEAVENLY_STEMS: dict[str, dict[str, str]] = {
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

EARTHLY_BRANCHES: dict[str, dict[str, object]] = {
    "子": {
        "ohaeng": "수",
        "yinyang": "양",
        "gijeong": {"癸": {"ohaeng": "수", "yinyang": "음"}},
    },
    "丑": {
        "ohaeng": "토",
        "yinyang": "음",
        "gijeong": {
            "己": {"ohaeng": "토", "yinyang": "음"},
            "癸": {"ohaeng": "수", "yinyang": "음"},
            "辛": {"ohaeng": "금", "yinyang": "음"},
        },
    },
    "寅": {
        "ohaeng": "목",
        "yinyang": "양",
        "gijeong": {
            "甲": {"ohaeng": "목", "yinyang": "양"},
            "丙": {"ohaeng": "화", "yinyang": "양"},
            "戊": {"ohaeng": "토", "yinyang": "양"},
        },
    },
    "卯": {
        "ohaeng": "목",
        "yinyang": "음",
        "gijeong": {
            "乙": {"ohaeng": "목", "yinyang": "음"},
        },
    },
    "辰": {
        "ohaeng": "토",
        "yinyang": "양",
        "gijeong": {
            "戊": {"ohaeng": "토", "yinyang": "양"},
            "乙": {"ohaeng": "목", "yinyang": "음"},
            "癸": {"ohaeng": "수", "yinyang": "음"},
        },
    },
    "巳": {
        "ohaeng": "화",
        "yinyang": "음",
        "gijeong": {
            "丙": {"ohaeng": "화", "yinyang": "양"},
            "戊": {"ohaeng": "토", "yinyang": "양"},
            "庚": {"ohaeng": "금", "yinyang": "양"},
        },
    },
    "午": {
        "ohaeng": "화",
        "yinyang": "양",
        "gijeong": {
            "丁": {"ohaeng": "화", "yinyang": "음"},
            "己": {"ohaeng": "토", "yinyang": "음"},
        },
    },
    "未": {
        "ohaeng": "토",
        "yinyang": "음",
        "gijeong": {
            "己": {"ohaeng": "토", "yinyang": "음"},
            "丁": {"ohaeng": "화", "yinyang": "음"},
            "乙": {"ohaeng": "목", "yinyang": "음"},
        },
    },
    "申": {
        "ohaeng": "금",
        "yinyang": "양",
        "gijeong": {
            "庚": {"ohaeng": "금", "yinyang": "양"},
            "壬": {"ohaeng": "수", "yinyang": "양"},
            "戊": {"ohaeng": "토", "yinyang": "양"},
        },
    },
    "酉": {
        "ohaeng": "금",
        "yinyang": "음",
        "gijeong": {
            "辛": {"ohaeng": "금", "yinyang": "음"},
        },
    },
    "戌": {
        "ohaeng": "토",
        "yinyang": "양",
        "gijeong": {
            "戊": {"ohaeng": "토", "yinyang": "양"},
            "辛": {"ohaeng": "금", "yinyang": "음"},
            "丁": {"ohaeng": "화", "yinyang": "음"},
        },
    },
    "亥": {
        "ohaeng": "수",
        "yinyang": "음",
        "gijeong": {
            "壬": {"ohaeng": "수", "yinyang": "양"},
            "甲": {"ohaeng": "목", "yinyang": "양"},
            "戊": {"ohaeng": "토", "yinyang": "양"},
        },
    },
}

# branch_hidden_stems는 지지별 지장간 이름만 필요한 경우를 위한 단축 데이터이다.
branch_hidden_stems: dict[str, list[str]] = {
    branch: list(data["gijeong"].keys()) for branch, data in EARTHLY_BRANCHES.items()
}

WUXING: dict[str, str] = {
    **{name: info["ohaeng"] for name, info in HEAVENLY_STEMS.items()},
    **{name: info["ohaeng"] for name, info in EARTHLY_BRANCHES.items()},
}

# --- 오행 상생/상극 및 십신 판정 규칙 --------------------------------------

WUXING_RELATIONS = {
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

CHEYONG_GROUPS = {
    "체": ["비견", "겁재", "정인", "편인"],
    "용": ["정재", "편재", "정관", "편관"],
    "중립": ["식신", "상관"],
}

MYOGO_BRANCHES = {"辰", "戌", "丑", "未"}

# --- 지지 관계 (형충파해합) --------------------------------------------------

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
PO = {("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("未", "戌")}
CHUAN = {("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")}
HAP = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}
SAMHAP = {
    ("寅", "午", "戌"): "화",
    ("巳", "酉", "丑"): "금",
    ("申", "子", "辰"): "수",
    ("亥", "卯", "未"): "목",
}

# --- 궁위 및 십신 기본 데이터 -----------------------------------------------

DEFAULT_GUNGWI_DATA = {
    "년주": {
        "life_stage": "유년 시기 (1-18세)",
        "representative_kin": "조상·부모·선배",
        "symbolic_meaning": "근본, 태생 환경, 원거리",
    },
    "월주": {
        "life_stage": "청년 시기 (18-35세)",
        "representative_kin": "부모·형제·사회적 기반",
        "symbolic_meaning": "출신 지역, 성장 배경",
    },
    "일주": {
        "life_stage": "장년 시기 (35-55세)",
        "representative_kin": "배우자·자아",
        "symbolic_meaning": "개인 가치관, 생활 중심",
    },
    "시주": {
        "life_stage": "말년 (55세 이후)",
        "representative_kin": "자녀·후배",
        "symbolic_meaning": "미래, 결과, 말년",
    },
}

DEFAULT_SHISHIN_DATA = {
    "비견": {"description": "자아, 동료, 평등 관계"},
    "겁재": {"description": "경쟁, 공유, 돌파"},
    "식신": {"description": "창조, 실행, 재능"},
    "상관": {"description": "표현, 개혁, 돌출"},
    "편재": {"description": "유동 자산, 기회"},
    "정재": {"description": "축적 자산, 현실"},
    "편관": {"description": "통제, 도전, 경쟁"},
    "정관": {"description": "규범, 명예, 책임"},
    "편인": {"description": "영감, 기획, 보호"},
    "정인": {"description": "학습, 지원, 문서"},
}

# --- 공망 기본 구조 (문서 파서 확장 시 채워짐) ------------------------------

GONGMANG_REFERENCE = {
    # 문서 파서를 통해 추가 데이터를 병합하기 위한 기본 형태.
    "설명": "공망은 특정 일주의 간지가 빠져 비어 있는 구간을 의미합니다.",
}
