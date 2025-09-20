# 📘 수암명리 AI 해석기

수암명리 룰셋(`rules.json`)과 OpenAI LLM을 결합하여 질문에 맞춘 해석을 제공하는 프로젝트입니다. Streamlit UI와 FastAPI 백엔드가 함께 제공되어 배포 환경에 맞게 선택적으로 사용할 수 있습니다.

## 📦 프로젝트 구조

```
suam_ai/
├── app.py               # Streamlit UI 진입점
├── main.py              # FastAPI 서버 (uvicorn으로 실행)
├── requirements.txt     # 필요한 패키지 목록
├── core/
│   ├── analyzer.py      # 룰셋 요약 및 기본 분석기
│   ├── context_builder.py # rules + 질문 → 컨텍스트 생성
│   ├── llm_chain.py     # LLM 체인 및 예외 처리
│   └── rules_loader.py  # rules.json 로더
├── data/
│   └── rules.json       # 통합 룰셋 (Book1~6 + 정리_GOO 예시 반영)
└── README.md            # 사용 가이드 (본 문서)
```

## 🔐 환경 변수 설정

1. `.env.example` 파일을 `.env`로 복사합니다.
2. 다음 값을 입력합니다.

```bash
OPENAI_API_KEY="sk-..."
```

> `.env`는 `.gitignore`에 포함되어 있어 원본 키가 저장소에 노출되지 않습니다. Streamlit의 비밀값을 사용하려면 `.streamlit/secrets.toml`에 동일한 키를 등록하세요.

## 🚀 설치 및 실행

```bash
# 의존성 설치
pip install -r suam_ai/requirements.txt

# Streamlit UI 실행
streamlit run suam_ai/app.py

# FastAPI 서버 실행
uvicorn suam_ai.main:app --reload --host 0.0.0.0 --port 8000
```

### API 예시

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
        "question": "이번 대운에서 혼인 응기가 있나요?",
        "saju": {"year": "戊辰", "month": "辛酉", "day": "己巳", "hour": "辛未", "gender": "female"}
      }'
```

`deterministic` 필드를 `true`로 지정하면 LLM을 호출하지 않고 룰셋 기반 요약을 반환합니다.

## ✅ 기본 동작

- **룰셋 로딩**: `rules_loader`가 `rules.json`을 검증하며, 누락/오류 시 사용자에게 한국어 경고를 제공합니다.
- **컨텍스트 생성**: `context_builder`가 질문과 사주 정보를 룰셋과 결합합니다.
- **LLM 호출**: `llm_chain`이 OpenAI Chat 모델(`gpt-4o-mini`)을 호출하며, API 키가 없거나 오류가 발생하면 룰셋 기반 요약으로 자동 대체합니다.
- **Streamlit UI**: 입력 폼과 함께 룰셋 요약을 병행 표시하여 검증에 도움이 됩니다.
- **FastAPI**: `/ask` 엔드포인트로 동일한 기능을 제공합니다. `/health`로 상태 확인이 가능합니다.

## 📄 룰셋 업데이트 가이드

- `data/rules.json`은 UTF-8 JSON 형식입니다.
- `analysis_order`, `event_conditions`, `exceptions`는 문자열 리스트로 관리합니다.
- `십성_변동`은 `{ "십성": "설명" }` 형태의 객체입니다.
- 포맷이 잘못되면 서비스가 중단되지 않고 경고 메시지를 노출합니다.

## 🧪 테스트

```bash
python -m compileall suam_ai
```

컴파일이 완료되면 주요 파이썬 모듈이 문법 오류 없이 배포 준비 상태임을 의미합니다.

## 📬 문의

새로운 기능을 추가할 때는 기존 기능이 정상 동작하는지 확인하고, `rules.json`과 `.env`에 민감한 정보를 안전하게 보관하세요.
