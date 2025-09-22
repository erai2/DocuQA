import streamlit as st
import os
import pandas as pd
from io import StringIO

from core.database import load_csv_files
from core.ai_engine import generate_ai_response, summarize_with_ai, clean_text_with_ai
from core.parsing import parse_and_store_documents

st.set_page_config(page_title="Suri Q&AI", layout="wide")
st.title("📊 Suri Q&AI")

# --- 1. 새 문서 업로드 + 파싱 ---
st.header("📑 새 문서 업로드 및 파싱")

uploaded_files = st.file_uploader(
    "txt/md 파일 업로드", 
    type=["txt", "md"], 
    accept_multiple_files=True
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

                # 🔹 DataFrame → CSV 문자열 변환
                raw_text = parsed_df.to_csv(index=False, encoding="utf-8-sig")

                # 🔹 AI 교정
                cleaned_text = clean_text_with_ai(raw_text)

                # 🔹 교정 결과를 다시 DataFrame으로 변환
                cleaned_df = pd.read_csv(StringIO(cleaned_text))

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
            else:
                st.warning("⚠️ 파싱 결과가 없습니다.")

# --- 2. CSV 데이터 관리 ---
st.header("📂 CSV 데이터 관리")
csv_dfs = load_csv_files("data")

if not csv_dfs:
    st.info("CSV 데이터가 없습니다. 먼저 업로드/파싱을 진행하세요.")
else:
    for name, df in csv_dfs.items():
        st.subheader(f"📑 {name}.csv")
        edited_df = st.data_editor(df, num_rows="dynamic", width="stretch")
        if st.button(f"{name}.csv 저장", key=f"save_{name}"):
            edited_df.to_csv(f"data/{name}.csv", index=False, encoding="utf-8-sig")
            st.success(f"{name}.csv 저장 완료 ✅")

# --- 3. AI 상담 (채팅창) ---
st.header("💬 AI 상담")

query = st.text_input("질문을 입력하세요:", key="user_query")
if st.button("AI 응답 생성"):
    if query.strip():
        answer = generate_ai_response(query)
        st.markdown(answer)
    else:
        st.warning("질문을 입력하세요.")

# --- 4. CSV 전체 요약 ---
st.header("📝 CSV 요약")
if st.button("CSV 전체 요약"):
    if not csv_dfs:
        st.warning("CSV 데이터가 없습니다.")
    else:
        try:
            combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
        except ValueError as exc:
            st.error(f"CSV 데이터를 결합하는 중 오류가 발생했습니다: {exc}")
            combined_df = None

        if combined_df is not None:
            # 🔹 DataFrame → CSV 문자열 변환 후 요약
            csv_text = combined_df.to_csv(index=False)
            summary = summarize_with_ai(csv_text)

            st.text_area("요약 결과", summary, height=300)

            if st.button("요약 결과 저장"):
                save_path = "data/summary.csv"
                pd.DataFrame([{"summary": summary}]).to_csv(save_path, index=False, encoding="utf-8-sig")
                st.success("요약 결과 저장 완료 ✅")

# --- 5. 키워드별 정리 ---
st.header("🔑 키워드별 문서 정리")

keywords_input = st.text_input("키워드를 콤마(,)로 구분해서 입력하세요 (예: 재물, 혼인, 직장, 건강)")
if st.button("키워드별 정리 실행"):
    if not csv_dfs:
        st.warning("CSV 데이터가 없습니다.")
    else:
        combined_df = pd.concat(list(csv_dfs.values()), ignore_index=True)
        csv_text = combined_df.to_csv(index=False)

        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
        if not keywords:
            st.warning("키워드를 입력하세요.")
        else:
            summary_by_kw = summarize_by_keywords(csv_text, keywords)
            st.text_area("키워드별 정리 결과", summary_by_kw, height=400)

