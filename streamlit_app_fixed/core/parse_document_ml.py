import re
import pandas as pd
from typing import List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# =============================
# 1. 간단한 학습용 데이터셋 (라벨링 필요)
# =============================
# 실제 프로젝트에서는 CSV나 DB에서 불러오는 게 좋음
TRAIN_DATA = [
    ("이 사례는 혼인 파탄 구조를 보여준다.", "case"),
    ("사례 1: 재물 손실 응기", "case"),
    ("다음 규칙에 따라 해석해야 한다.", "rule"),
    ("관성은 반드시 인성과 함께 작용해야 한다는 규칙", "rule"),
    ("관성의 정의는 직장·명예와 관련된다.", "concept"),
    ("록과 원신의 개념을 먼저 이해해야 한다.", "concept"),
]

# =============================
# 2. ML 파이프라인 (TF-IDF + LogisticRegression)
# =============================
def train_model(train_data=TRAIN_DATA) -> Pipeline:
    texts, labels = zip(*train_data)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=200))
    ])

    pipeline.fit(X_train, y_train)

    # 테스트 출력
    y_pred = pipeline.predict(X_test)
    print("[INFO] 샘플 데이터 성능:")
    print(classification_report(y_test, y_pred))

    return pipeline

MODEL = train_model()

# =============================
# 3. 문서 파싱 함수
# =============================
def parse_document_ml(text: str) -> Tuple[List[dict], List[dict], List[dict]]:
    """
    문서를 줄 단위로 분리 → ML 분류기로 case/rule/concept 분류
    """
    cases, rules, concepts = [], [], []
    lines = text.splitlines()

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        label = MODEL.predict([clean_line])[0]

        if label == "case":
            cases.append({"detail": clean_line})
        elif label == "rule":
            rules.append({"desc": clean_line})
        elif label == "concept":
            concepts.append({"desc": clean_line})

    return cases, rules, concepts
