# 📘 수암명리 AI 해석기 (DocuQA 확장)

이 저장소는 기존 DocuQA 실험에 더해 **수암명리 룰셋 + LLM 파이프라인**을 제공합니다. `suam_ai` 디렉터리에는 Streamlit UI와 FastAPI API 서버, 룰셋 로더가 포함되어 있으며, 배포 전 단계에서 오류 없이 실행할 수 있도록 구성되었습니다.

## 📂 구성

```
DocuQA/
├── suam_ai/              # 수암명리 파이프라인 (주요 작업 디렉터리)
│   ├── app.py            # Streamlit UI
│   ├── main.py           # FastAPI 진입점
│   ├── core/             # 룰셋/컨텍스트/LLM 유틸리티
│   ├── data/rules.json   # 통합 룰셋 (예시 데이터)
│   └── README.md         # 세부 실행 가이드
├── streamlit_app_fixed/  # 기존 DocuQA 하이브리드 검색 예제 (옵션)
├── .env.example          # 환경 변수 템플릿
└── README.md             # 현재 문서
```

## 🔧 설치

```bash
pip install -r suam_ai/requirements.txt
```

필요한 패키지: `streamlit`, `fastapi`, `uvicorn`, `langchain`, `langchain-openai`, `openai`, `python-dotenv`, `pydantic`.

## 🔐 환경 변수 & 보안

1. `.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`를 입력합니다.
2. `.env`, `.streamlit/secrets.toml`은 `.gitignore`에 포함되어 민감 정보가 버전 관리에 노출되지 않습니다.
3. 서버 배포 시에는 운영 환경 변수(예: Docker, Cloud Run)로 키를 주입하는 것을 권장합니다.

## ▶️ 실행 방법

### Streamlit UI
```bash
streamlit run suam_ai/app.py
```

### FastAPI 서버
```bash
uvicorn suam_ai.main:app --reload --host 0.0.0.0 --port 8000
```

- `/health`: 상태 확인
- `/ask`: 질문/사주 데이터를 POST로 전달하여 분석 결과 수신
- `deterministic=true` 옵션으로 룰셋 기반 요약만 받을 수 있습니다.

## 🧪 테스트

```bash
python -m compileall suam_ai
```

컴파일이 통과하면 주요 스크립트가 문법 오류 없이 배포 준비 상태임을 의미합니다.

## 🛠️ 개선 사항 요약

- 프로젝트 구조를 `suam_ai` 기준으로 재정리하고, import 경로를 표준화했습니다.
- `rules_loader`, `context_builder`, `llm_chain`, `analyzer`를 분리하여 유지보수를 용이하게 했습니다.
- LLM 호출 실패 시 룰셋 기반 요약으로 자동 대체하도록 예외 처리를 강화했습니다.
- `.env` 템플릿과 `.gitignore` 규칙을 정비하여 민감 정보가 안전하게 관리됩니다.

## 📄 추가 참고

- `suam_ai/README.md`에서 상세 가이드를 확인하세요.
- 기존 `streamlit_app_fixed` 폴더는 레거시 하이브리드 검색 대시보드 예제로 남아 있으며 필요 시 참고할 수 있습니다.
