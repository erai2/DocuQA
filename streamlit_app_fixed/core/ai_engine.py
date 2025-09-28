# core/ai_engine.py
from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

def generate_ai_response(query: str) -> str:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.3))
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    prompt = PromptTemplate(
        input_variables=["query"],
        template="다음 질문에 대해 수암명리 관점에서 논리적으로 해석해 주세요:\n\n{query}",
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"query": query})

def summarize_long_csv(csv_text: str) -> Tuple[str, List[str]]:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    lines = csv_text.splitlines()
    chunk_size = 200
    parts = [lines[i:i+chunk_size] for i in range(0, len(lines), chunk_size)]
    summaries: List[str] = []
    for idx, part in enumerate(parts, start=1):
        prompt = PromptTemplate(
            input_variables=["chunk"],
            template=f"다음 CSV 일부를 요약해 주세요 (Part {idx}):\n\n{{chunk}}",
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        summary = chain.run({"chunk": "\n".join(part)})
        summaries.append(summary.strip())
    overall_prompt = PromptTemplate(
        input_variables=["summaries"],
        template="다음 요약들을 종합하여 전체 CSV 핵심 요약을 작성해 주세요:\n\n{summaries}",
    )
    overall_chain = LLMChain(llm=llm, prompt=overall_prompt)
    overall_summary = overall_chain.run({"summaries": "\n".join(summaries)})
    return overall_summary.strip(), summaries

def summarize_by_keywords(csv_text: str, keywords: List[str]) -> str:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0.2)
    keywords_str = ", ".join(keywords)
    prompt = PromptTemplate(
        input_variables=["csv_text", "keywords"],
        template=("다음 CSV 내용을 검토하고 주어진 키워드({keywords})와 관련된 부분만 발췌 요약해 주세요.\n\n{csv_text}"),
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"csv_text": csv_text, "keywords": keywords_str}).strip()
