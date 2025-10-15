"""Streamlit application for automated Notion analysis."""
from __future__ import annotations

from typing import Iterable

import streamlit as st

from modules import parser, ai_requester, notion_connector, db_manager


SENSITIVE_KEYWORDS: Iterable[str] = (".env", ".gitignore", ".streamlit")


st.set_page_config(page_title="Suam Notion AI 자동 분석기", layout="wide")
st.title("📘 수암명리 Notion-AI 자동 분석기")


uploaded = st.file_uploader("문서를 업로드하세요", type=["txt", "pdf", "docx"])


if uploaded:
    filename = uploaded.name or ""
    lowered_name = filename.lower()
    if any(keyword in lowered_name for keyword in SENSITIVE_KEYWORDS):
        st.error("🚫 보안이 필요한 문서는 업로드할 수 없습니다. (.env, .gitignore, .streamlit 등)")
    else:
        try:
            text = parser.extract_text(uploaded)
        except Exception as exc:  # pragma: no cover - Streamlit runtime
            st.error(f"문서를 읽는 중 오류가 발생했습니다: {exc}")
        else:
            st.text_area("📄 미리보기", text[:500], height=200)

            if st.button("🔍 자동 분석 및 Notion 전송"):
                sentences = parser.split_sentences(text)
                valid_sentences = [s for s in sentences if len(s.strip()) >= 5]

                if not valid_sentences:
                    st.warning("분석할 문장이 없습니다. 문서를 확인해주세요.")
                else:
                    results = []
                    progress = st.progress(0.0)

                    for idx, sentence in enumerate(valid_sentences, start=1):
                        try:
                            structured = ai_requester.structurize(sentence, "자동분류")
                            notion_id = notion_connector.send_to_notion(sentence, structured["tags"])
                            structured["notion_id"] = notion_id
                            db_manager.save_to_json(structured)
                            db_manager.save_to_sqlite(structured)
                        except Exception as exc:  # pragma: no cover - Streamlit runtime
                            st.error(f"문장 처리 중 오류가 발생했습니다: {exc}")
                            continue

                        results.append(structured)
                        progress.progress(idx / len(valid_sentences))

                    if results:
                        st.success(f"✅ 분석 완료! {len(results)}개 문장을 Notion과 로컬에 저장했습니다.")
                        st.json(results[:5])
                    else:
                        st.warning("정상적으로 처리된 문장이 없습니다.")
else:
    st.info("문서를 업로드하면 자동 분석을 시작할 수 있습니다.")
