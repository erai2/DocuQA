# core/parse_document_ml.py
import openai

def parse_document_ml(text: str):
    """
    AI 기반으로 문서를 규칙/사례/용어로 분류
    """
    chunks = [p.strip() for p in text.split("\n") if p.strip()]
    cases, rules, concepts = [], [], []

    for idx, chunk in enumerate(chunks):
        prompt = f"""
        너는 수암명리 텍스트 분류기야.
        아래 문장이 규칙(rule), 사례(case), 용어(concept) 중 어디에 해당하는지 판정해.
        - 규칙(rule): 형/충/합/파/천/묘고 등 원리 설명
        - 사례(case): 실제 사주팔자, 응기 사례
        - 용어(concept): 록, 원신, 대상, 환상 등 개념 정의
        문장: {chunk}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            label = response.choices[0].message["content"].strip().lower()

            if "rule" in label or "규칙" in label:
                rules.append({"id": f"rule_{idx}", "desc": chunk})
            elif "case" in label or "사례" in label:
                cases.append({"id": f"case_{idx}", "detail": chunk})
            else:
                concepts.append({"id": f"concept_{idx}", "desc": chunk})

        except Exception as e:
            print(f"[ERROR] ML 파싱 실패: {e}")
            concepts.append({"id": f"concept_{idx}", "desc": chunk})

    return cases, rules, concepts
