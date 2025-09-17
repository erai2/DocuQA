import pandas as pd
import os

def parse_and_store_documents(file_path: str):
    """
    문서를 파싱하고 DataFrame으로 반환
    - 항상 pandas.DataFrame 반환 보장
    - 에러 발생 시 빈 DataFrame 반환
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 예시 파싱: 줄 단위로 저장
        records = [
            {"filename": os.path.basename(file_path), "line": i, "text": line.strip()}
            for i, line in enumerate(content.splitlines(), start=1)
            if line.strip()
        ]

        if not records:
            return pd.DataFrame()

        df = pd.DataFrame(records)

        # parsed_docs.csv에 누적 저장
        parsed_csv = "data/parsed_docs.csv"
        os.makedirs("data", exist_ok=True)
        if not df.empty:
            if os.path.exists(parsed_csv):
                old_df = pd.read_csv(parsed_csv)
                combined = pd.concat([old_df, df], ignore_index=True).drop_duplicates()
            else:
                combined = df
            combined.to_csv(parsed_csv, index=False, encoding="utf-8-sig")

        return df

    except Exception as e:
        print(f"[ERROR] parse_and_store_documents 실패: {e}")
        return pd.DataFrame()
