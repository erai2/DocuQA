# 📘 DocuQA Streamlit Suite

이 저장소는 문서 업로드·파싱·검색을 한 번에 처리할 수 있는 **Streamlit 기반 Q&A 대시보드**를 제공합니다. `streamlit_app_fixed/` 디렉터리에는
문서를 규칙 기반/AI 기반으로 파싱하고, 하이브리드 검색 및 OpenAI API를 활용한 분석 기능이 구현되어 있습니다.

최근 정리 과정에서 불필요한 `codex` 브랜치 산출물을 제거하고, 원래의 Streamlit 앱 기능을 보존하도록 파일 구조를 정리했습니다.

## 📂 디렉터리 구조

```
DocuQA/
├── streamlit_app_fixed/
│   ├── main.py               # Streamlit 진입점 (문서 관리 + 인물 프로필)
│   ├── profiles_page.py      # 인물 프로필 편집 페이지
│   ├── core/                 # 파싱·AI·DB·검색 유틸리티 모음
│   ├── data/                 # 예시 문서 및 벡터 DB가 저장되는 디렉터리
│   └── requirements.txt      # 앱 실행에 필요한 패키지 목록
├── .env.example              # OpenAI 키 템플릿 (실제 키는 .env에 저장)
├── .gitignore                # 민감 정보 및 캐시 무시 규칙
└── README.md                 # 현재 문서
```

> 🔐 `streamlit_app_fixed/.streamlit/secrets.toml`과 `.env` 파일은 민감 정보를 담을 수 있으므로 Git에서 제외되어 있습니다.

## 🔧 설치 및 환경 설정

1. Python 3.10 이상의 가상환경을 생성합니다.
2. 필수 패키지를 설치합니다.

```bash
pip install -r streamlit_app_fixed/requirements.txt
```

3. 환경 변수 템플릿을 복사해 OpenAI API 키를 설정합니다.

```bash
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 값을 실제 키로 수정하세요.
```

필요 시 `streamlit_app_fixed/.streamlit/secrets.toml` 파일에 Streamlit 비밀 키를 추가할 수 있습니다. 해당 파일은 버전 관리에서 제외되어 있으므로
배포 환경에서 직접 작성하세요.

## ▶️ 실행 방법

아래 명령으로 Streamlit 대시보드를 실행할 수 있습니다.

```bash
streamlit run streamlit_app_fixed/main.py
```

대시보드는 다음과 같은 기능을 제공합니다.

- **문서 업로드 및 파싱**: txt/md 파일을 규칙 기반, AI 보조, 하이브리드 방식으로 구조화합니다.
- **AI 교정 및 요약**: OpenAI API를 사용해 파싱 결과를 정리하고 CSV 요약·키워드 정리를 수행합니다.
- **하이브리드 검색**: TF-IDF와 벡터 검색을 조합해 관련 문서를 탐색합니다.
- **인물 프로필 관리**: `profiles_page.py`에서 인물 정보를 CRUD 방식으로 관리할 수 있습니다.

## 🧪 테스트

앱이 사용하는 모듈이 정상적으로 컴파일되는지 확인하려면 다음 명령을 실행하세요.

```bash
python -m compileall streamlit_app_fixed
```

추가적인 테스트 스크립트나 CI가 필요하다면 `streamlit_app_fixed/core` 모듈을 기준으로 확장할 수 있습니다.

## 📄 참고

- `.env`와 `.streamlit` 내부 파일은 반드시 로컬/배포 환경에서만 관리하여 보안을 유지하세요.
- `streamlit_app_fixed/data` 폴더에는 예시 문서를 제공합니다. 실제 서비스 환경에서는 적절한 저장소나 DB로 대체하세요.
