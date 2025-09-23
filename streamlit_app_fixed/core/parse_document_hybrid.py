# core/parse_document_hybrid.py
import re
import json
import openai

def parse_document_hybrid(text: str, batch_size=5, model="gpt-4o-mini"):
    """
    Hybrid Parser:
    1단계: 규칙 기반 → 확실한 것 자동 분류
    2단계: 남은 것만 AI 태깅
    """
    rules, cases, concepts = [], [], []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    uncertain = []

    for idx, line in enumerate(lines):
        if any(kw in line for kw in ["合","沖","冲","刑","破","穿","入墓","墓庫"]):
            rules.append({"id": f"rule_{idx}", "desc": line})
        elif re.search(r"[甲乙丙丁戊己庚辛壬癸].*[子丑寅卯辰巳午未申酉戌亥]", line):
            cases.append({"id": f"case_{idx}", "detail": line})
        elif any(kw in line for kw in ["祿","元神","原神","帶象","幻象","空亡","驛馬"]):
            concepts.append({"id": f"concept_{idx}", "desc": line})
        else:
            uncertain.append((idx, line))

    for i in range(0, len(uncertain), batch_size):
        batch = uncertain[i:i+batch_size]
        texts = [line for _, line in batch]

        prompt = f"""
        너는 수암명리 텍스트 분류기야.
        아래 문장들을 규칙(rule), 사례(case), 용어(concept) 중 어디에 해당하는지 JSON 배열로 분류해.
        JSON 구조:
        [
          {{"type":"rule","content":"..." }},
          {{"type":"case","content":"..." }},
          {{"type":"concept","content":"..." }}
        ]

        문장들:
        {json.dumps(texts, ensure_ascii=False)}
        """
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            result = json.loads(response.choices[0].message["content"])
            for j, item in enumerate(result):
                idx = batch[j][0]
                if item["type"] == "rule":
                    rules.append({"id": f"rule_{idx}", "desc": item["content"]})
                elif item["type"] == "case":
                    cases.append({"id": f"case_{idx}", "detail": item["content"]})
                else:
                    concepts.append({"id": f"concept_{idx}", "desc": item["content"]})
        except Exception as e:
            print(f"[ERROR] Hybrid ML 파싱 실패: {e}")
            for j, (_, line) in enumerate(batch):
                concepts.append({"id": f"concept_{i+j}", "desc": line})

    return cases, rules, concepts
