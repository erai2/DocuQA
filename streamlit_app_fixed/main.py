import streamlit as st
import os
import pandas as pd
from io import StringIO

# Core 모듈
from core.database import ensure_db, insert_csv_to_db, load_csv_from_db, load_csv_files
from core.hybrid_search import hybrid_search
from core.ai_engine import (
    generate_ai_response,
    ask_csv_ai,
    summarize_long_csv,
    summarize_by_keywords,
    clean_text_with_ai,
)
from core.parsing import parse_and_store_documents

# =============================
# 페이지 기본 설정
# =============================
st.set_page_config(page_title="Suri Q&AI", layout="wide")
st.title("📊 Suri Q&AI (최신 OpenAI API 버전)")

# =============================
# 1. 새 문서 업로드 및 파싱
# =============================
st.header("📑 새 문서 업로드 및 파싱")

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
            os.makedirs("data/raw_docs", exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            parsed_df = parse_and_store_documents(save_path)

            if parsed_df is not None and isinstance(parsed_df, pd.DataFrame) and not parsed_df.empty:
                st.success("✅ 파싱 완료, AI 교정 적용 중...")

                # DataFrame → CSV 문자열 변환
                raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")

                # AI 교정
                cleaned_text = clean_text_with_ai(raw_text)

                try:
                    cleaned_df = pd.read_csv(StringIO(cleaned_text))
                except Exception as e:
                    st.error(f"AI 교정 후 CSV 변환 실패: {e}")
                    cleaned_df = parsed_df

                st.success("✅ AI 교정 완료! 아래에서 직접 수정 후 저장하세요.")
                edited_df = st.data_editor(cleaned_df, num_rows="dynamic", width="stretch")

                if st.button(f"{uploaded_file.name} 저장", key=f"save_{uploaded_file.name}"):
                    parsed_csv = "data/parsed_docs.csv"
                    if os.path.exists(parsed_csv):
                        old_df = pd.read_csv(parsed_csv)
                        combined = pd.concat([old_df, edited_df], ignore_index=True).drop_duplicates()
                    else:
                        combined = edited_df

                    combined.to_csv(parsed_csv, index=False, encoding="utf-8-sig")
                    st.success("📂 parsed_docs.csv 저장 완료 ✅")

                    # 🔹 DB에도 반영
                    ensure_db()
                    insert_csv_to_db(combined, table_name="parsed_docs")
                    st.success("📦 DB에도 저장 완료 ✅")
            else:
                st.warning("⚠️ 파싱 결과가 없습니다.")

# =============================
# 2. CSV 데이터 관리
# =============================
st.header("📂 CSV 데이터 관리")
csv_dfs = load_csv_files("data")

# 🔹 DB 불러오기 기능
if st.button("DB에서 불러오기"):
    ensure_db()
    db_df = load_csv_from_db("parsed_docs")
    if db_df is not None and not db_df.empty:
        st.subheader("📦 DB 불러오기 결과")
        st.dataframe(db_df, width="stretch")

if not csv_dfs:
    st.info("CSV 데이터가 없습니다. 먼저 업로드/파싱을 진행하세요.")
else:
    for name, df in csv_dfs.items():
        st.subheader(f"📑 {name}.csv")

        # 원본 CSV → 문자열 변환
        csv_text = df.to_csv(index=False, encoding="utf-8-sig")

        if st.button(f"{name}.csv AI 교정 적용", key=f"clean_{name}"):
            st.info("AI 교정 중...")
            cleaned_text = clean_text_with_ai(csv_text)
            try:
                df = pd.read_csv(StringIO(cleaned_text))
                st.success("✅ AI 교정 완료! 아래에서 직접 수정 후 저장하세요.")
            except Exception as e:
                st.error(f"AI 교정 후 CSV 변환 실패: {e}")

        edited_df = st.data_editor(df, num_rows="dynamic", width="stretch")

        if st.button(f"{name}.csv 저장", key=f"save_{name}"):
            save_path = f"data/{name}.csv"
            edited_df.to_csv(save_path, index=False, encoding="utf-8-sig")
            st.success(f"{name}.csv 저장 완료 ✅")

            # DB에도 저장
            ensure_db()
            insert_csv_to_db(edited_df, table_name=name)
            st.success(f"📦 {name} → DB 저장 완료 ✅")

# =============================
# 3. AI 상담 (벡터/하이브리드 검색)
# =============================
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

# =============================
# 4. CSV 요약
# =============================
st.header("📝 CSV 요약")
if st.button("CSV 전체 요약"):
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

# =============================
# 5. 키워드별 정리
# =============================
st.header("🔑 키워드별 문서 정리")

keywords_input = st.text_input("키워드를 콤마(,)로 구분해서 입력하세요 (예: 재물, 혼인, 직장, 건강)")
if st.button("키워드별 정리 실행"):
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
