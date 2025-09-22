import os
import subprocess
import uvicorn
import argparse
from backend import parser as parser_module
from backend import rules_extractor

def run_parser(folder="./documents"):
    print("📂 Step 1: 문서 파싱 시작...")
    parser_module.init_db()
    parser_module.process_folder(folder)

def run_rules_extractor():
    print("📖 Step 2: 규칙 확장 시작...")
    rules_extractor.expand_rules()

def run_server():
    print("🚀 Step 3: FastAPI 서버 실행 중 (http://localhost:8000)...")
    uvicorn.run("backend.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocuQA 통합 실행기")
    parser.add_argument("--folder", type=str, default="./documents", help="문서 폴더 경로")
    parser.add_argument("--no-parser", action="store_true", help="파서 건너뛰기")
    parser.add_argument("--no-rules", action="store_true", help="규칙 추출 건너뛰기")
    args = parser.parse_args()

    if not args.no_parser:
        run_parser(args.folder)
    if not args.no_rules:
        run_rules_extractor()
    run_server()
