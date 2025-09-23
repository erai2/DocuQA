import streamlit as st
import os
import pandas as pd
from io import StringIO

# =============================
# core 모듈 불러오기
# =============================
from core.database import (
    ensure_db,
    insert_csv_to_db,
    load_csv_from_db,
    load_csv_files,
    list_tables,
)
from core.hybrid_search import hybrid_search
from core.ai_engine import (
    generate_ai_response,
    ask_csv_ai,
    summarize_long_csv,
    summarize_by_keywords,
)
from core.ai_utils import clean_text_with_ai
from core.rag import build_databases
from profiles_page import profiles_page

# =============================
# 초기 세팅
# =============================
st.set_page_config(page_title="Suri Q&AI", layout="wide")
st.title("📊 Suri Q&AI (최신 OpenAI API 버전)")

for path in ["data", "data/raw_docs", "data/vector_db"]:
    os.makedirs(path, exist_ok=True)
ensure_db()

# =============================
# 페이지 라우팅
# =============================
PAGES = {
    "문서 관리": "main_page",
    "인물 프로필": profiles_page,
}
page_choice = st.sidebar.radio("📌 페이지 선택", list(PAGES.keys()))

# =============================
# 1. 문서 관리 페이지
# =============================
if page_choice == "문서 관리":

    # -------------------------
    # 1-1. 새 문서 업로드 및 파싱
    # -------------------------
    st.header("📑 새 문서 업로드 및 파싱")

    parser_mode = st.radio(
        "파서 모드 선택",
        ["1단계: 규칙 기반 (빠름)", "2단계: AI 보조 (정밀)", "3단계: Hybrid (효율적)"],
        horizontal=True
    )

    uploaded_files = st.file_uploader(
        "txt/md 파일 업로드", type=["txt", "md"], accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.read().decode("utf-8")
            st.subheader(f"📄 {uploaded_file.name}")
            st.text_area("파일 내용 미리보기", file_content[:1000], height=200)

            if st.button(f"이 문서 파싱하기: {uploaded_file.name}"):
                save_path = os.path.join("data/raw_docs", uploaded_file.name)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                # 파서 모드 선택
                rows = []
                if "규칙 기반" in parser_mode:
                    from core.parsing import parse_document
                    cases, rules, concepts = parse_document(file_content)
                elif "AI 보조" in parser_mode:
                    from core.parse_document_ml import parse_document_ml
                    cases, rules, concepts = parse_document_ml(file_content)
                else:
                    from core.parse_document_hybrid import parse_document_hybrid
                    cases, rules, concepts = parse_document_hybrid(file_content)

                # 결과 → DataFrame
                for c in cases:
                    rows.append({"type": "case", "id": c["id"], "content": c.get("detail", "")})
                for r in rules:
                    rows.append({"type": "rule", "id": r["id"], "content": r.get("desc", "")})
                for c in concepts:
                    rows.append({"type": "concept", "id": c["id"], "content": c.get("desc", "")})
                parsed_df = pd.DataFrame(rows)

                if parsed_df is not None and not parsed_df.empty:
                    st.success("✅ 파싱 완료, AI 교정 적용 중...")

                    raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")
                    cleaned_text = clean_text_with_ai(raw_text)

                    try:
                        cleaned_df = pd.read_csv(StringIO(cleaned_text))
                    except Exception as e:
                        st.error(f"AI 교정 후 CSV 변환 실패: {e}")
                        cleaned_df = parsed_df

                    st.success("✅ AI 교정 완료! 아래에서 직접 수정 후 저장하세요.")
                    edited_df = st.data_editor(cleaned_df, num_rows="dynamic", use_container_width=True)

                    if st.button(f"{uploaded_file.name} 저장", key=f"save_{uploaded_file.name}"):
                        parsed_csv = "data/parsed_docs.csv"
                        if os.path.exists(parsed_csv):
                            old_df = pd.read_csv(parsed_csv)
                            combined = pd.concat([old_df, edited_df], ignore_index=True).drop_duplicates()
                        else:
                            combined = edited_df

                        combined.to_csv(parsed_csv, index=False, encoding="utf-8-sig")
                        st.success(f"📂 parsed_docs.csv 저장 완료 (총 {len(combined)}행) ✅")

                        total_rows = insert_csv_to_db(combined, table_name="parsed_docs")
                        st.success(f"📦 DB 저장 완료: {total_rows}행 (중복 제거 후)")
                else:
                    st.warning("⚠️ 파싱 결과가 없습니다.")

    # -------------------------
    # 1-2. DB 데이터 확인
    # -------------------------
    st.header("📦 DB 데이터 확인")
    if st.button("DB에서 불러오기"):
        db_df = load_csv_from_db("parsed_docs")
        if not db_df.empty:
            st.subheader("📦 DB 불러오기 결과")
            st.dataframe(db_df, use_container_width=True)
        else:
            st.warning("⚠️ DB에 데이터가 없습니다.")

    # -------------------------
    # 1-3. CSV 요약
    # -------------------------
    st.header("📝 CSV 요약")
    if st.button("CSV 전체 요약"):
        csv_dfs = load_csv_files("data")
        if not csv_dfs:
            st.warning("CSV 데이터가 없습니다.")
        else:
            try:
                combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
                csv_text = combined_df.to_csv(index=False, encoding="utf-8-sig")
                summary, parts = summarize_long_csv(csv_text)
                st.text_area("CSV 전체 요약 결과", summary, height=300)
                with st.expander("부분 요약 보기"):
                    for part in parts:
                        st.markdown(part)
            except ValueError as exc:
                st.error(f"CSV 결합 오류: {exc}")

    # -------------------------
    # 1-4. 키워드별 정리
    # -------------------------
    st.header("🔑 키워드별 문서 정리")
    keywords_input = st.text_input("키워드를 콤마(,)로 입력 (예: 재물, 혼인, 직장, 건강)")
    if st.button("키워드별 정리 실행"):
        csv_dfs = load_csv_files("data")
        if not csv_dfs:
            st.warning("CSV 데이터가 없습니다.")
        else:
            combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
            csv_text = combined_df.to_csv(index=False, encoding="utf-8-sig")
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
            if not keywords:
                st.warning("키워드를 입력하세요.")
            else:
                summary_by_kw = summarize_by_keywords(csv_text, keywords)
                st.text_area("키워드별 정리 결과", summary_by_kw, height=400)

    # -------------------------
    # 1-5. AI 상담
    # -------------------------
    st.header("💬 AI 상담")
    query = st.text_input("질문을 입력하세요:", key="user_query")
    search_mode = st.radio("검색 모드 선택", ["벡터 검색", "하이브리드 검색"], horizontal=True)

    if st.button("AI 응답 생성"):
        if query.strip():
            if search_mode == "하이브리드 검색":
                docs = hybrid_search(query, db_dir="data/vector_db", k=5)
                context = "\n\n".join([d.page_content for d in docs])
                answer = generate_ai_response(f"{query}\n\n참고자료:\n{context}")
            else:
                answer = generate_ai_response(query)
            st.markdown(answer)
        else:
            st.warning("질문을 입력하세요.")

    # -------------------------
    # 1-6. DB 빌드
    # -------------------------
    st.header("🛠️ 데이터베이스 빌드")
    if st.button("데이터베이스 빌드 실행"):
        with st.spinner("문서를 파싱하고 DB/VectorDB를 빌드 중..."):
            vs = build_databases(data_dir="data/raw_docs", db_dir="data/vector_db")
        if vs:
            st.success("✅ DB 및 VectorDB 빌드 완료")
        else:
            st.warning("⚠️ 빌드할 문서가 없습니다.")

    # -------------------------
    # 1-7. DB 관리
    # -------------------------
    st.header("🗂️ DB 관리")
    if st.button("테이블 목록 보기"):
        tables = list_tables()
        if tables:
            st.write("📋 현재 DB 테이블 목록:")
            st.write(tables)
        else:
            st.info("DB에 테이블이 없습니다.")

    tables = list_tables()
    if tables:
        selected_table = st.selectbox("조회할 테이블 선택", tables, key="view_table")
        if st.button("테이블 불러오기"):
            df = load_csv_from_db(selected_table)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("⚠️ 데이터가 없습니다.")

        del_table = st.selectbox("삭제할 테이블 선택", tables, key="delete_table")
        if st.button("테이블 삭제"):
            import sqlite3
            conn = sqlite3.connect("suri_m.db")
            cur = conn.cursor()
            cur.execute(f"DROP TABLE IF EXISTS {del_table}")
            conn.commit()
            conn.close()
            st.success(f"🗑️ {del_table} 테이블 삭제 완료")

# =============================
# 2. 인물 프로필 페이지
# =============================
elif page_choice == "인물 프로필":
    profiles_page()
