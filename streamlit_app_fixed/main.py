"""Streamlit entrypoint for the Suri Q&AI application."""

from __future__ import annotations

import os
from io import StringIO
from typing import Dict, Iterable, List

import pandas as pd
import streamlit as st

from core.ai_engine import generate_ai_response, summarize_by_keywords, summarize_long_csv
from core.ai_utils import clean_text_with_ai
from core.database import (
    ensure_db,
    insert_csv_to_db,
    load_csv_files,
    load_csv_from_db,
    list_tables,
)
from core.hybrid_search import hybrid_search
from core.rag import build_databases
from profiles_page import profiles_page


DATA_DIR = "data"
RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_docs")
VECTOR_DB_DIR = os.path.join(DATA_DIR, "vector_db")
PARSED_CSV_PATH = os.path.join(DATA_DIR, "parsed_docs.csv")

RULE_CATEGORIES = [
    "궁위 (Gung-wi)",
    "십신 허투 (Heo-tu)",
    "대상 (Dae-sang)",
    "묘고 (Mooko)",
    "상호작용 규칙",
]

PRIORITY_LEVELS = [
    "1. 구조 결정",
    "2. 특수 구조",
    "3. 허투/입묘",
    "4. 일반론",
]

CASE_FOCUS_TOPICS = [
    "직업/사회운",
    "가족/육친",
    "재물운",
    "건강/학업운",
]


def configure_app() -> None:
    """Set default layout information and bootstrap directories/database."""

    st.set_page_config(page_title="Suri Q&AI", layout="wide")
    st.title("📊 Suri Q&AI (최신 OpenAI API 버전)")

    ensure_directories([DATA_DIR, RAW_DOCS_DIR, VECTOR_DB_DIR])
    ensure_db()


def ensure_directories(paths: Iterable[str]) -> None:
    """Create directories required by the application if they do not exist."""

    for path in paths:
        os.makedirs(path, exist_ok=True)


def render_document_management_page() -> None:
    """Render the document management workflow."""

    render_upload_section()
    render_db_preview_section()
    render_rule_case_dashboard()
    render_csv_summary_section()
    render_keyword_summary_section()
    render_chatbot_workflow_section()
    render_ai_consultation_section()
    render_database_build_section()
    render_database_management_section()


def render_upload_section() -> None:
    st.header("📑 새 문서 업로드 및 파싱")

    parser_mode = st.radio(
        "파서 모드 선택",
        ["1단계: 규칙 기반 (빠름)", "2단계: AI 보조 (정밀)", "3단계: Hybrid (효율적)"],
        horizontal=True,
    )

    uploaded_files = st.file_uploader(
        "txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True
    )

    if not uploaded_files:
        return

    for uploaded_file in uploaded_files:
        file_content = uploaded_file.read().decode("utf-8")
        st.subheader(f"📄 {uploaded_file.name}")
        st.text_area("파일 내용 미리보기", file_content[:1000], height=200)

        if not st.button(f"이 문서 파싱하기: {uploaded_file.name}"):
            continue

        save_path = os.path.join(RAW_DOCS_DIR, uploaded_file.name)
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(file_content)

        parsed_df = parse_document_by_mode(file_content, parser_mode)
        if parsed_df.empty:
            st.warning("⚠️ 파싱 결과가 없습니다.")
            continue

        st.success("✅ 파싱 완료, AI 교정 적용 중...")

        raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")
        cleaned_df = clean_dataframe_with_ai(raw_text, parsed_df)

        st.success("✅ AI 교정 완료! 아래에서 직접 수정 후 저장하세요.")
        edited_df = st.data_editor(
            cleaned_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config=build_editor_column_config(),
            column_order=[
                "type",
                "id",
                "category",
                "priority_tier",
                "focus_topic",
                "keywords",
                "content",
                "principle_summary",
                "analysis",
                "chart",
                "day_master",
                "core_principles",
                "source_document",
            ],
            disabled=["type", "id"],
        )

        if st.button(f"{uploaded_file.name} 저장", key=f"save_{uploaded_file.name}"):
            combined = merge_with_existing_csv(edited_df)
            combined.to_csv(PARSED_CSV_PATH, index=False, encoding="utf-8-sig")
            st.success(f"📂 parsed_docs.csv 저장 완료 (총 {len(combined)}행) ✅")

            total_rows = insert_csv_to_db(combined, table_name="parsed_docs")
            st.success(f"📦 DB 저장 완료: {total_rows}행 (중복 제거 후)")


def parse_document_by_mode(file_content: str, parser_mode: str) -> pd.DataFrame:
    """Parse documents using the selected parsing strategy and enrich with taxonomy fields."""

    rows: List[Dict[str, str]] = []

    if "규칙 기반" in parser_mode:
        from core.parsing import parse_document

        cases, rules, concepts = parse_document(file_content)
    elif "AI 보조" in parser_mode:
        from core.parse_document_ml import parse_document_ml

        cases, rules, concepts = parse_document_ml(file_content)
    else:
        from core.parse_document_hybrid import parse_document_hybrid

        cases, rules, concepts = parse_document_hybrid(file_content)

    for case in cases:
        rows.append({"type": "case", "id": case["id"], "content": case.get("detail", "")})
    for rule in rules:
        rows.append({"type": "rule", "id": rule["id"], "content": rule.get("desc", "")})
    for concept in concepts:
        rows.append({"type": "concept", "id": concept["id"], "content": concept.get("desc", "")})

    return build_structured_dataframe(rows)


def build_structured_dataframe(rows: List[Dict[str, str]]) -> pd.DataFrame:
    """Return a DataFrame seeded with 수암 명리 taxonomy columns for downstream editing."""

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df.fillna("")
    df["category"] = df["type"].map(
        {
            "case": "사례",
            "rule": "미분류",
            "concept": "미분류",
        }
    ).fillna("미분류")
    df["priority_tier"] = df["type"].map(
        {
            "case": "",
            "rule": PRIORITY_LEVELS[0],
            "concept": PRIORITY_LEVELS[0],
        }
    )
    df["focus_topic"] = df["type"].map({"case": CASE_FOCUS_TOPICS[0]}).fillna("")
    df["keywords"] = ""
    df["source_document"] = ""
    df["principle_summary"] = ""
    df["analysis"] = ""
    df["chart"] = ""
    df["day_master"] = ""
    df["core_principles"] = ""

    # Ensure deterministic column order for editors and CSV exports
    ordered_columns = [
        "type",
        "id",
        "category",
        "priority_tier",
        "focus_topic",
        "keywords",
        "content",
        "principle_summary",
        "analysis",
        "chart",
        "day_master",
        "core_principles",
        "source_document",
    ]
    existing_columns = [col for col in ordered_columns if col in df.columns]
    remaining_columns = [col for col in df.columns if col not in existing_columns]
    return df[existing_columns + remaining_columns]


def build_editor_column_config() -> Dict[str, st.column_config.BaseColumn]:
    """Build Streamlit column configuration for the structured editor."""

    return {
        "type": st.column_config.TextColumn("분류", help="원본 추출 타입 (사례/규칙/개념)"),
        "id": st.column_config.TextColumn("원문 ID"),
        "category": st.column_config.SelectboxColumn(
            "핵심 카테고리",
            options=["미분류"] + RULE_CATEGORIES + ["사례"],
            help="수암 명리 핵심 원리 분류를 선택하세요.",
        ),
        "priority_tier": st.column_config.SelectboxColumn(
            "우선순위",
            options=[""] + PRIORITY_LEVELS,
            help="수암 명리 구조론 우선순위를 지정합니다.",
        ),
        "focus_topic": st.column_config.SelectboxColumn(
            "주요 해석 주제",
            options=[""] + CASE_FOCUS_TOPICS,
            help="사례의 해석 주제를 태그하세요.",
        ),
        "keywords": st.column_config.TextColumn(
            "핵심 키워드",
            help="검색용 키워드를 콤마로 입력하세요.",
        ),
        "content": st.column_config.TextColumn(
            "원문/설명",
            help="문서에서 추출한 핵심 내용을 정리하세요.",
        ),
        "principle_summary": st.column_config.TextColumn(
            "원리 요약",
            help="간략한 요약 또는 정리 문장을 작성하세요.",
        ),
        "analysis": st.column_config.TextColumn(
            "해석 노트",
            help="구조 판단 또는 추가 메모를 작성하세요.",
        ),
        "chart": st.column_config.TextColumn(
            "명식 (사례)",
            help="사례일 경우 사주 명식을 입력하세요.",
        ),
        "day_master": st.column_config.TextColumn(
            "일간",
            help="사례의 일간을 기입하세요.",
        ),
        "core_principles": st.column_config.TextColumn(
            "적용 원칙",
            help="사례에서 활용된 핵심 원칙을 나열하세요.",
        ),
        "source_document": st.column_config.TextColumn(
            "출처 문서",
            help="자료의 출처 파일명을 기록하세요.",
        ),
    }


def clean_dataframe_with_ai(raw_text: str, fallback_df: pd.DataFrame) -> pd.DataFrame:
    """Apply AI-powered cleaning to the parsed dataframe, falling back to original data."""

    cleaned_text = clean_text_with_ai(raw_text)
    try:
        cleaned_df = pd.read_csv(StringIO(cleaned_text))
        return align_to_reference_columns(cleaned_df, fallback_df.columns.tolist())
    except Exception as exc:  # pragma: no cover - defensive logging for UI
        st.error(f"AI 교정 후 CSV 변환 실패: {exc}")
        return fallback_df


def merge_with_existing_csv(edited_df: pd.DataFrame) -> pd.DataFrame:
    """Merge edited dataframe with existing parsed CSV data, removing duplicates."""

    if os.path.exists(PARSED_CSV_PATH):
        old_df = pd.read_csv(PARSED_CSV_PATH).fillna("")
        target_columns = build_union_columns(edited_df, old_df)
        old_df_aligned = align_to_reference_columns(old_df, target_columns)
        new_df_aligned = align_to_reference_columns(edited_df, target_columns)
        combined = pd.concat([old_df_aligned, new_df_aligned], ignore_index=True)
        combined = deduplicate_structured_rows(combined)
        return combined

    return edited_df


def build_union_columns(*frames: pd.DataFrame) -> List[str]:
    """Return a deterministic union of columns, preserving order of the first dataframe."""

    if not frames:
        return []

    ordered = list(frames[0].columns)
    for frame in frames[1:]:
        for column in frame.columns:
            if column not in ordered:
                ordered.append(column)
    return ordered


def align_to_reference_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Ensure a dataframe contains the reference columns, filling missing values."""

    aligned = df.copy()
    for column in columns:
        if column not in aligned.columns:
            aligned[column] = ""
    aligned = aligned.fillna("")
    # Preserve reference order while keeping any additional columns at the end
    extra_columns = [col for col in aligned.columns if col not in columns]
    return aligned[columns + extra_columns]


def deduplicate_structured_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicated structured rows while respecting key 수암 명리 columns."""

    candidate_columns = [
        "type",
        "id",
        "content",
        "category",
        "chart",
        "day_master",
        "analysis",
    ]
    subset = [col for col in candidate_columns if col in df.columns]
    if not subset:
        return df.drop_duplicates()
    return df.drop_duplicates(subset=subset)


def render_db_preview_section() -> None:
    st.header("📦 DB 데이터 확인")

    if not st.button("DB에서 불러오기"):
        return

    db_df = load_csv_from_db("parsed_docs")
    if db_df.empty:
        st.warning("⚠️ DB에 데이터가 없습니다.")
        return

    st.subheader("📦 DB 불러오기 결과")
    st.dataframe(db_df, use_container_width=True)


def render_csv_summary_section() -> None:
    st.header("📝 CSV 요약")

    if not st.button("CSV 전체 요약"):
        return

    csv_text = build_combined_csv_text()
    if not csv_text:
        st.warning("CSV 데이터가 없습니다.")
        return

    try:
        summary, parts = summarize_long_csv(csv_text)
    except ValueError as exc:
        st.error(f"CSV 결합 오류: {exc}")
        return

    st.text_area("CSV 전체 요약 결과", summary, height=300)
    with st.expander("부분 요약 보기"):
        for part in parts:
            st.markdown(part)


def build_combined_csv_text() -> str:
    """Combine CSV files from the data directory into a single CSV text blob."""

    csv_dfs = load_csv_files(DATA_DIR)
    if not csv_dfs:
        return ""

    combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
    return combined_df.to_csv(index=False, encoding="utf-8-sig")


def render_keyword_summary_section() -> None:
    st.header("🔑 키워드별 문서 정리")
    keywords_input = st.text_input("키워드를 콤마(,)로 입력 (예: 재물, 혼인, 직장, 건강)")

    if not st.button("키워드별 정리 실행"):
        return

    csv_text = build_combined_csv_text()
    if not csv_text:
        st.warning("CSV 데이터가 없습니다.")
        return

    keywords = [keyword.strip() for keyword in keywords_input.split(",") if keyword.strip()]
    if not keywords:
        st.warning("키워드를 입력하세요.")
        return

    summary_by_kw = summarize_by_keywords(csv_text, keywords)
    st.text_area("키워드별 정리 결과", summary_by_kw, height=400)


def render_rule_case_dashboard() -> None:
    st.header("📚 수암 명리 Rule/Case 대시보드")

    df = load_csv_from_db("parsed_docs")
    if df.empty:
        st.info("DB에 구조화된 데이터가 없습니다. 먼저 문서를 파싱해 저장하세요.")
        return

    df = df.fillna("")
    rule_df = df[df["type"] != "case"]
    case_df = df[df["type"] == "case"]

    cols = st.columns(2)
    with cols[0]:
        st.subheader("핵심 원리 카테고리 분포")
        if rule_df.empty:
            st.write("원리 데이터가 아직 없습니다.")
        else:
            category_counts = (
                rule_df.groupby("category")["content"].count().reset_index(name="entries")
            )
            priority_counts = (
                rule_df.groupby("priority_tier")["content"].count().reset_index(name="entries")
            )
            st.dataframe(category_counts, use_container_width=True)
            with st.expander("우선순위별 원리 현황"):
                st.dataframe(priority_counts, use_container_width=True)

    with cols[1]:
        st.subheader("사례 태그 현황")
        if case_df.empty:
            st.write("사례 데이터가 아직 없습니다.")
        else:
            focus_counts = (
                case_df.groupby("focus_topic")["content"].count().reset_index(name="entries")
            )
            st.dataframe(focus_counts, use_container_width=True)

    if not case_df.empty:
        st.markdown("---")
        focus_topic = st.selectbox(
            "자세히 보고 싶은 주제 선택",
            ["전체"] + CASE_FOCUS_TOPICS,
            key="case_focus_filter",
        )
        filtered_cases = (
            case_df if focus_topic == "전체" else case_df[case_df["focus_topic"] == focus_topic]
        )
        if filtered_cases.empty:
            st.warning("해당 주제로 태그된 사례가 없습니다.")
        else:
            view_columns = [
                col
                for col in [
                    "chart",
                    "day_master",
                    "core_principles",
                    "analysis",
                    "source_document",
                ]
                if col in filtered_cases.columns
            ]
            st.dataframe(filtered_cases[view_columns + ["content"]], use_container_width=True)


def render_chatbot_workflow_section() -> None:
    st.header("🔮 수암 명리 챗봇 해석 엔진")

    col1, col2 = st.columns(2)
    with col1:
        birth_year = st.text_input("출생 년 (YYYY)", key="suan_birth_year")
        birth_month = st.text_input("출생 월 (MM)", key="suan_birth_month")
        birth_day = st.text_input("출생 일 (DD)", key="suan_birth_day")
        birth_hour = st.text_input("출생 시 (HH 또는 지지)", key="suan_birth_hour")
    with col2:
        gender = st.selectbox(
            "성별", ["선택 안 함", "남성", "여성"], key="suan_gender_select"
        )
        focus_topic = st.selectbox(
            "가장 궁금한 분야", CASE_FOCUS_TOPICS, key="suan_focus_topic_select"
        )
        additional_question = st.text_area(
            "추가 질문 또는 상황", height=120, key="suan_additional_question"
        )

    if st.button("수암 명리 해석 생성"):
        if not (birth_year and birth_month and birth_day and birth_hour):
            st.warning("생년월일시 정보를 모두 입력하세요.")
            return

        with st.spinner("수암 명리 구조 분석 중..."):
            context_payload = load_structured_context()
            prompt = build_interpretation_prompt(
                birth_year,
                birth_month,
                birth_day,
                birth_hour,
                gender,
                focus_topic,
                additional_question,
                context_payload,
            )
            response = generate_ai_response(prompt)

        st.markdown("### 🧭 수암 명리 3단계 해석")
        st.markdown(response)
        with st.expander("사용된 분석 프롬프트 보기"):
            st.code(prompt)


def load_structured_context() -> Dict[str, str]:
    """Load structured rule/case context from the database to enrich chatbot prompts."""

    df = load_csv_from_db("parsed_docs")
    if df.empty:
        return {"rules": "", "cases": ""}

    df = df.fillna("")
    rule_sections: List[str] = []
    case_sections: List[str] = []

    rule_df = df[df["type"] != "case"]
    if not rule_df.empty:
        for category in RULE_CATEGORIES:
            category_df = rule_df[rule_df["category"] == category]
            if category_df.empty:
                continue
            lines = []
            for _, row in category_df.iterrows():
                summary = row.get("principle_summary") or row.get("content", "")
                priority = row.get("priority_tier", "")
                if priority:
                    lines.append(f"- ({priority}) {summary}")
                else:
                    lines.append(f"- {summary}")
            rule_sections.append(f"[{category}]\n" + "\n".join(lines))

    case_df = df[df["type"] == "case"]
    if not case_df.empty:
        for topic in CASE_FOCUS_TOPICS:
            topic_df = case_df[case_df["focus_topic"] == topic]
            if topic_df.empty:
                continue
            lines = []
            for _, row in topic_df.iterrows():
                chart = row.get("chart", "")
                principles = row.get("core_principles") or row.get("analysis") or row.get("content", "")
                lines.append(f"- {chart}: {principles}")
            case_sections.append(f"[{topic}]\n" + "\n".join(lines))

    return {"rules": "\n\n".join(rule_sections), "cases": "\n\n".join(case_sections)}


def build_interpretation_prompt(
    birth_year: str,
    birth_month: str,
    birth_day: str,
    birth_hour: str,
    gender: str,
    focus_topic: str,
    additional_question: str,
    context_payload: Dict[str, str],
) -> str:
    """Compose a structured prompt implementing the 3-step 수암 명리 해석 프로세스."""

    gender_text = gender if gender != "선택 안 함" else "미지정"
    user_context = additional_question.strip() or "추가 질문 없음"

    rule_context = context_payload.get("rules", "")
    case_context = context_payload.get("cases", "")

    prompt = f"""
당신은 수암 명리 스타일의 전문 해석가입니다. 아래의 데이터베이스를 활용하여 논리적이고 단계적인 상담을 제공합니다.

[사용자 입력]
- 생년월일시: {birth_year}-{birth_month}-{birth_day} {birth_hour}
- 성별: {gender_text}
- 주요 관심사: {focus_topic}
- 추가 배경/질문: {user_context}

[수암 명리 핵심 원리 DB]
{rule_context or '등록된 원리가 부족합니다. 기본 원리와 문맥을 사용하세요.'}

[수암 명리 사례 DB]
{case_context or '등록된 사례가 부족합니다. 일반적 사례 추론을 적용하세요.'}

3단계 절차에 따라 답변하세요.
1단계 (명식 생성 및 기본 분석): 입력된 생년월일시를 바탕으로 간단한 명식을 추정하고 십신 배치를 개략적으로 설명합니다.
2단계 (핵심 인자 추출 및 우선순위 적용): 구조론 우선순위(1. 제압/합충형 공, 2. 궁위·대상·묘고 등 특수 구조, 3. 허투/입묘, 4. 일반 십신 해석)를 순차적으로 점검하고 핵심 포인트를 요약합니다.
3단계 (사용자 맞춤 해석): 선택된 관심 주제({focus_topic})를 중심으로 직관적인 상담 문장을 제시하고, 필요하다면 대운/세운 변화를 간단히 조언합니다.

각 단계를 명확한 소제목으로 구분하고, 수암 명리 용어를 한국어로 유지하면서 이해하기 쉬운 문장으로 작성하세요. 마지막에는 핵심 키워드를 불릿으로 정리하세요.
"""

    return prompt.strip()


def render_ai_consultation_section() -> None:
    st.header("💬 AI 상담")

    query = st.text_input("질문을 입력하세요:", key="user_query")
    search_mode = st.radio(
        "검색 모드 선택", ["벡터 검색", "하이브리드 검색"], horizontal=True
    )

    if not st.button("AI 응답 생성"):
        return

    if not query.strip():
        st.warning("질문을 입력하세요.")
        return

    if search_mode == "하이브리드 검색":
        docs = hybrid_search(query, db_dir=VECTOR_DB_DIR, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        answer = generate_ai_response(f"{query}\n\n참고자료:\n{context}")
    else:
        answer = generate_ai_response(query)

    st.markdown(answer)


def render_database_build_section() -> None:
    st.header("🛠️ 데이터베이스 빌드")

    if not st.button("데이터베이스 빌드 실행"):
        return

    with st.spinner("문서를 파싱하고 DB/VectorDB를 빌드 중..."):
        vs = build_databases(data_dir=RAW_DOCS_DIR, db_dir=VECTOR_DB_DIR)

    if vs:
        st.success("✅ DB 및 VectorDB 빌드 완료")
    else:
        st.warning("⚠️ 빌드할 문서가 없습니다.")


def render_database_management_section() -> None:
    st.header("🗂️ DB 관리")

    if st.button("테이블 목록 보기"):
        tables = list_tables()
        if tables:
            st.write("📋 현재 DB 테이블 목록:")
            st.write(tables)
        else:
            st.info("DB에 테이블이 없습니다.")

    tables = list_tables()
    if not tables:
        return

    selected_table = st.selectbox("조회할 테이블 선택", tables, key="view_table")
    if st.button("테이블 불러오기"):
        df = load_csv_from_db(selected_table)
        if df.empty:
            st.warning("⚠️ 데이터가 없습니다.")
        else:
            st.dataframe(df, use_container_width=True)

    del_table = st.selectbox("삭제할 테이블 선택", tables, key="delete_table")
    if st.button("테이블 삭제"):
        drop_table(del_table)


def drop_table(table_name: str) -> None:
    """Safely drop a table from the SQLite database used by the app."""

    import sqlite3

    with sqlite3.connect("suri_m.db") as conn:
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()

    st.success(f"🗑️ {table_name} 테이블 삭제 완료")


def main() -> None:
    configure_app()
    page_choice = st.sidebar.radio("📌 페이지 선택", ["문서 관리", "인물 프로필"])

    if page_choice == "문서 관리":
        render_document_management_page()
    else:
        profiles_page()


if __name__ == "__main__":
    main()
