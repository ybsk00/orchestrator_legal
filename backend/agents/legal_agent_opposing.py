"""
법무 시뮬레이션 에이전트: 변호인/피고대리 (Opposing)

역할:
- 형사: 피고인측 변호인 (Defense Counsel)
- 민사: 피고측 변호사 (Defendant Counsel)

기능:
- 반박, 항변, 절차적 문제점, 반증 전략
- 민사: 합의안 제시 (SettlementOptions)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.legal.role_prompts import (
    LEGAL_STEERING_BLOCK,
    OPPOSING_PROMPT,
    get_opposing_role_label,
    get_case_type_label,
)


class LegalAgentOpposing(BaseAgent):
    """변호인/피고대리 (Opposing) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
        self._case_type = "civil"
        self._confirmed_facts = ""
        self._case_summary = ""
    
    @property
    def role_name(self) -> str:
        return "opposing"
    
    @property
    def system_prompt(self) -> str:
        # 템플릿 변수 치환
        prompt = OPPOSING_PROMPT.replace("{{opposing_role}}", get_opposing_role_label(self._case_type))
        prompt = prompt.replace("{{case_type_label}}", get_case_type_label(self._case_type))
        prompt = prompt.replace("{{confirmed_facts}}", self._confirmed_facts or "없음")
        prompt = prompt.replace("{{case_summary}}", self._case_summary or "없음")
        
        return prompt
    
    def set_round(self, round_number: int):
        """라운드 설정"""
        self._current_round = round_number
    
    def set_case_context(
        self, 
        case_type: str, 
        confirmed_facts: str = "", 
        case_summary: str = ""
    ):
        """사건 컨텍스트 설정"""
        self._case_type = case_type
        self._confirmed_facts = confirmed_facts
        self._case_summary = case_summary
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        base_schema = {
            "type": "object",
            "properties": {
                "counter_arguments": {"type": "array", "items": {"type": "string"}},
                "disproof_plan": {"type": "array", "items": {"type": "string"}},
                "procedural_risks": {"type": "array", "items": {"type": "string"}},
            }
        }
        
        # 민사 사건에서만 합의안 포함
        if self._case_type == "civil":
            base_schema["properties"]["settlement_options"] = {
                "type": "array", 
                "items": {"type": "string"}
            }
        
        return base_schema
