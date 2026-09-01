import os
from typing import Optional, Dict, Any, List
import structlog
from pydantic import BaseModel, Field

logger=structlog.get_logger(__name__)

class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_in: int=0
    tokens_out: int=0
    latency_ms: float=0.0

FEW_SHOT_ATTACK_EXAMPLES = [
    {
        "scenario": "idor",
        "input": "Target: juice_shop, Endpoint: /api/users/1, Objective: Horizontal IDOR",
        "output": '{"technique_id":"T1548.003","owasp_category":"A01","attack_type":"horizontal_idor","payload":{"id":2},"reason":"Enum adjacent user IDs to test BOLA"}'
    },
    {
        "scenario": "injection",
        "input": "Target: dvwa, Endpoint: /vulnerabilities/sqli/, Objective: SQLi",
        "output": '{"technique_id":"T1190","owasp_category":"A03","attack_type":"sql_injection","payload":{"id":"1\' OR \'1\'=\'1"},"reason":"Classic auth bypass via tautology"}'
    },
    {
        "scenario": "ssrf",
        "input": "Target: custom, Endpoint: /api/fetch?url=, Objective: SSRF to cloud metadata",
        "output": '{"technique_id":"T1590","owasp_category":"A10","attack_type":"cloud_metadata_access","payload":{"url":"http://169.254.169.254/latest/meta-data/"},"reason":"Access IMDS for credential exfiltration"}'
    },
]

SYSTEM_PROMPT_BASE = """You are a Purple Team security agent. Respond ONLY with valid JSON matching the requested schema. No markdown fences. No explanation outside JSON."""

def _build_few_shot_system(scenario: str, json_mode: bool) -> str:
    if not json_mode:
        return SYSTEM_PROMPT_BASE
    examples = [e for e in FEW_SHOT_ATTACK_EXAMPLES if e["scenario"]==scenario][:2]
    if not examples:
        examples = FEW_SHOT_ATTACK_EXAMPLES[:2]
    few = "\n".join([f"Example Input: {e['input']}\nExample Output: {e['output']}" for e in examples])
    return f"{SYSTEM_PROMPT_BASE}\n\nFew-shot examples (follow same pattern):\n{few}\n\nAlways return single JSON object, keys: technique_id, owasp_category, attack_type, payload, reason."

class LLMClient:
    """Local-first LLM client: Ollama primary, Groq/OpenRouter fallback, stub if neither available (for CI/tests)."""
    def __init__(self, model: Optional[str]=None, temperature: float=0.2):
        self.ollama_url=os.getenv("OLLAMA_URL","http://localhost:11434")
        self.ollama_model=model or os.getenv("OLLAMA_MODEL","llama3.1:8b")
        self.groq_key=os.getenv("GROQ_API_KEY")
        self.openrouter_key=os.getenv("OPENROUTER_API_KEY")
        self.temperature=temperature
        self._stub_index = 0  # rotate stub outputs for determinism without repetition

    async def ainvoke(self, prompt: str, system: Optional[str]=None, json_mode: bool=False) -> LLMResponse:
        # Enrich system with few-shot if not provided and json_mode
        if system is None and json_mode:
            # infer scenario from prompt
            scen = "idor"
            for cand in ["injection","ssrf","business_logic","broken_auth","idor"]:
                if cand in prompt.lower():
                    scen = cand
                    break
            system = _build_few_shot_system(scen, json_mode=True)
        elif system and json_mode and "Example" not in system:
            system = system + "\n" + _build_few_shot_system("idor", json_mode=True)
        # Try Ollama via langchain-ollama if available
        try:
            from langchain_ollama import ChatOllama
            import time
            llm=ChatOllama(model=self.ollama_model, base_url=self.ollama_url, temperature=self.temperature, format="json" if json_mode else None)
            msgs=[]
            if system: msgs.append(("system", system))
            msgs.append(("human", prompt))
            t0=time.time()
            resp=await llm.ainvoke(msgs)
            latency=(time.time()-t0)*1000
            content=resp.content if hasattr(resp,"content") else str(resp)
            return LLMResponse(content=content, model=self.ollama_model, latency_ms=latency)
        except Exception as e:
            logger.warning("Ollama failed, trying Groq/OpenRouter fallback", error=str(e))
        # Groq fallback
        if self.groq_key:
            try:
                from langchain_groq import ChatGroq
                import time
                llm=ChatGroq(model="llama3-8b-8192", api_key=self.groq_key, temperature=self.temperature)
                t0=time.time()
                resp=await llm.ainvoke(prompt)
                latency=(time.time()-t0)*1000
                return LLMResponse(content=resp.content, model="groq:llama3-8b-8192", latency_ms=latency)
            except Exception as e2:
                logger.warning("Groq failed", error=str(e2))
        # OpenRouter fallback
        if self.openrouter_key:
            try:
                import httpx
                import time
                t0=time.time()
                async with httpx.AsyncClient(timeout=30) as c:
                    r=await c.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization":f"Bearer {self.openrouter_key}"}, json={"model":"qwen/qwen-2.5-7b-instruct","messages":[{"role":"user","content":prompt}],"temperature":self.temperature})
                    r.raise_for_status()
                    j=r.json()
                    content=j["choices"][0]["message"]["content"]
                    return LLMResponse(content=content, model="openrouter:qwen2.5-7b", latency_ms=(time.time()-t0)*1000)
            except Exception as e3:
                logger.warning("OpenRouter failed", error=str(e3))
        # Stub for offline/test - rotate few-shot examples deterministically instead of fixed JSON
        logger.info("LLM stub fallback", prompt=prompt[:80])
        if json_mode:
            # rotate through few-shot examples to avoid single-technique bias
            example = FEW_SHOT_ATTACK_EXAMPLES[self._stub_index % len(FEW_SHOT_ATTACK_EXAMPLES)]
            self._stub_index += 1
            # if prompt hints at scenario, prefer matching example
            for e in FEW_SHOT_ATTACK_EXAMPLES:
                if e["scenario"] in prompt.lower():
                    example = e
                    break
            stub = example["output"]
        else:
            stub = "Stub LLM response: no provider configured. Using deterministic fallback with few-shot pattern."
        return LLMResponse(content=stub, model="stub", latency_ms=5.0)

    async def structured(self, prompt: str, schema: type[BaseModel], system: Optional[str]=None) -> BaseModel:
        resp=await self.ainvoke(prompt, system=system, json_mode=True)
        import json
        try:
            data=json.loads(resp.content)
            # handle markdown code fences
            if isinstance(data,str):
                data=json.loads(data)
            return schema.model_validate(data)
        except Exception:
            # fallback: try to extract json
            import re
            m=re.search(r"\{.*\}", resp.content, re.S)
            if m:
                return schema.model_validate(json.loads(m.group(0)))
            raise

_llm_singleton: Optional[LLMClient]=None
def get_llm(model: Optional[str]=None) -> LLMClient:
    global _llm_singleton
    if _llm_singleton is None or (model and _llm_singleton.ollama_model!=model):
        _llm_singleton=LLMClient(model=model)
    return _llm_singleton
