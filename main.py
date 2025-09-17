import pandas as pd
import os

with tab2:
    st.header("데이터베이스 관리 (CSV 편집기)")

    data_dir = "data"
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")]

    if csv_files:
        selected_file = st.selectbox("편집할 CSV 파일 선택", csv_files)
        file_path = os.path.join(data_dir, selected_file)

        # CSV 불러오기
        df = pd.read_csv(file_path)

        st.subheader(f"📂 {selected_file} 내용")
        st.caption("👉 셀을 직접 수정하거나 행을 추가/삭제할 수 있습니다.")

        # 수정 가능한 데이터 편집기
        edited_df = st.data_editor(df, num_rows="dynamic")

        # 저장 버튼
        if st.button("변경사항 저장"):
            edited_df.to_csv(file_path, index=False, encoding="utf-8-sig")
            st.success(f"{selected_file} 저장 완료 ✅")
    else:
        st.info("아직 CSV 파일이 없습니다. `/data` 폴더에 CSV 파일을 추가하세요.")
