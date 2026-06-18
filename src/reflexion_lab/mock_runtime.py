from __future__ import annotations
import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv
from .schemas import QAExample, JudgeResult, ReflectionEntry
from .prompts import ACTOR_SYSTEM, EVALUATOR_SYSTEM, REFLECTOR_SYSTEM
from .utils import normalize_answer

load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class LLMResponse:
    def __init__(self, content: str, tokens: int, latency_ms: int):
        self.content = content
        self.tokens = tokens
        self.latency_ms = latency_ms


def parse_json(text: str) -> dict:
    import re
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    text = text.replace("\n", " ").replace("\r", "").replace("\t", " ")
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    for i in range(len(text)):
        if text[i] == '{':
            depth = 0
            for j in range(i, len(text)):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[i:j+1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            break
            break
    print(f"[DEBUG] Could not parse JSON from: {text[:500]}")
    return {"score": 0, "reason": "Parse error", "missing_evidence": [], "spurious_claims": []}


def actor_answer(example: QAExample, attempt_id: int, agent_type: str, reflection_memory: list[str]) -> LLMResponse:
    context_str = "\n".join(f"[{c.title}] {c.text}" for c in example.context)
    history = ""
    if reflection_memory:
        history = "\n\nPrevious attempts lessons:\n" + "\n".join(reflection_memory)

    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ACTOR_SYSTEM},
            {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {example.question}{history}\n\nAnswer:"}
        ],
        temperature=0,
    )
    latency_ms = int((time.time() - start) * 1000)
    tokens = response.usage.total_tokens
    return LLMResponse(content=response.choices[0].message.content.strip(), tokens=tokens, latency_ms=latency_ms)


def evaluator(example: QAExample, answer: str) -> tuple[JudgeResult, LLMResponse]:
    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EVALUATOR_SYSTEM},
            {"role": "user", "content": f"Question: {example.question}\nGold answer: {example.gold_answer}\nPredicted answer: {answer}\n\nReturn JSON:"}
        ],
        temperature=0,
    )
    latency_ms = int((time.time() - start) * 1000)
    tokens = response.usage.total_tokens
    data = parse_json(response.choices[0].message.content)
    try:
        return JudgeResult(**data), LLMResponse(content="", tokens=tokens, latency_ms=latency_ms)
    except Exception:
        fallback = JudgeResult(score=0, reason="Parse error - could not evaluate")
        return fallback, LLMResponse(content="", tokens=tokens, latency_ms=latency_ms)


def reflector(example: QAExample, attempt_id: int, judge: JudgeResult) -> tuple[ReflectionEntry, LLMResponse]:
    start = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": REFLECTOR_SYSTEM},
            {"role": "user", "content": f"Question: {example.question}\nWrong answer reason: {judge.reason}\nAttempt ID: {attempt_id}\n\nReturn JSON:"}
        ],
        temperature=0,
    )
    latency_ms = int((time.time() - start) * 1000)
    tokens = response.usage.total_tokens
    data = parse_json(response.choices[0].message.content)
    try:
        return ReflectionEntry(**data), LLMResponse(content="", tokens=tokens, latency_ms=latency_ms)
    except Exception:
        fallback = ReflectionEntry(
            attempt_id=attempt_id,
            failure_reason=judge.reason,
            lesson="Focus on completing all reasoning hops",
            next_strategy="Read context carefully and answer step by step"
        )
        return fallback, LLMResponse(content="", tokens=tokens, latency_ms=latency_ms)


FAILURE_MODE_BY_QID = {}
