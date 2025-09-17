import streamlit as st
import os
import pandas as pd

from core.database import ensure_db, insert_sample_data, load_csv_files
from core.ai_engine import generate_ai_response, summarize_with_ai
from core.parsing import parse_and_store_documents

st.set_page_config(page_title="suri Q&AI", layout="wide")
st.title("📊 suri Q&AI")

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
            # 저장
            save_path = os.path.join("data/raw_docs", uploaded_file.name)
            os.makedirs("data/raw_docs", exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(file_content)

            # 파싱 실행
            parsed_df = parse_and_store_documents(save_path)

            if parsed_df is not None and isinstance(parsed_df, pd.DataFrame) and not parsed_df.empty:
                st.success("✅ 파싱 완료, 결과 확인")
                st.dataframe(parsed_df, width="stretch")

                # parsed_docs.csv 누적 저장
                parsed_csv = "data/parsed_docs.csv"
                if os.path.exists(parsed_csv):
                    old_df = pd.read_csv(parsed_csv)
                    combined = pd.concat([old_df, parsed_df], ignore_index=True).drop_duplicates()
                else:
                    combined = parsed_df
                combined.to_csv(parsed_csv, index=False, encoding="utf-8-sig")
                st.success("📂 parsed_docs.csv 에 반영 완료")
            else:
                st.warning(⚠️ 파싱 결과가 없습니다.")

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

# --- CSV 전체 요약 ---
st.header("📝 CSV 요약")
if st.button("CSV 전체 요약"):
    if not csv_dfs:
        st.warning("CSV 데이터가 없습니다.")
    else:
        combined_text = "\n".join([df.to_string() for df in csv_dfs.values()])
        summary = summarize_with_ai(combined_text)
        st.text_area("요약 결과", summary, height=300)

        if st.button("요약 결과 저장"):
            save_path = "data/summary.csv"
            pd.DataFrame([{"summary": summary}]).to_csv(save_path, index=False, encoding="utf-8-sig")
            st.success("요약 결과 저장 완료 ✅")
