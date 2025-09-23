import streamlit as st
import sqlite3
import pandas as pd
from core.ai_engine import generate_ai_response

DB_PATH = "suri_m.db"

def ensure_profiles_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            birthdata TEXT,
            notes TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            role TEXT,
            content TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def load_profiles():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM profiles", conn)
    conn.close()
    return df

def save_profile(name, birthdata, notes=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO profiles (name, birthdata, notes) VALUES (?,?,?)",
                (name, birthdata, notes))
    conn.commit()
    conn.close()

def save_chat(profile_id, role, content):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO profile_chat (profile_id, role, content) VALUES (?,?,?)",
                (profile_id, role, content))
    conn.commit()
    conn.close()

def load_chat(profile_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT role, content FROM profile_chat WHERE profile_id=? ORDER BY id DESC LIMIT 10",
                     conn, params=(profile_id,))
    conn.close()
    return df

# -----------------------
# Streamlit UI
# -----------------------
def profiles_page():
    st.title("👤 인물 프로필 관리")

    ensure_profiles_table()

    # 새 프로필 추가
    with st.expander("➕ 새 프로필 추가"):
        name = st.text_input("이름")
        birthdata = st.text_input("사주 원국 (예: 甲子年 丙申月 庚午日 戊辰時)")
        notes = st.text_area("스토리 메모")
        if st.button("저장"):
            save_profile(name, birthdata, notes)
            st.success("✅ 프로필 저장 완료")

    # 프로필 카드 표시
    profiles = load_profiles()
    if profiles.empty:
        st.info("아직 등록된 프로필이 없습니다.")
    else:
        for _, row in profiles.iterrows():
            with st.container():
                st.subheader(f"📌 {row['name']}")
                st.write(f"**사주 원국**: {row['birthdata']}")
                st.write(f"📝 {row['notes'][:100]}...")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("오늘의 운세", key=f"fortune_{row['id']}"):
                        fortune = generate_ai_response(f"{row['birthdata']} 오늘의 운세를 알려줘")
                        st.success(fortune)

                with col2:
                    question = st.text_input(f"{row['name']}에게 질문:", key=f"q_{row['id']}")
                    if st.button("질문하기", key=f"ask_{row['id']}") and question.strip():
                        answer = generate_ai_response(f"[사주: {row['birthdata']}] {row['notes']} 참고\n\n질문: {question}")
                        save_chat(row['id'], "user", question)
                        save_chat(row['id'], "assistant", answer)
                        st.markdown(answer)

                # 최근 대화 기록
                chat_df = load_chat(row['id'])
                if not chat_df.empty:
                    with st.expander("💬 최근 대화"):
                        for _, chat in chat_df.iterrows():
                            role = "🙂" if chat['role']=="user" else "🤖"
                            st.write(f"{role} {chat['content']}")
