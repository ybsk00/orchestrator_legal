"""
법무 시뮬레이션 에이전트: 검사/원고대리 (Claimant)

역할:
- 형사: 검사 (Prosecutor)
- 민사: 원고측 변호사 (Plaintiff Counsel)

기능:
- 주장 구성, 요건사실 분석, 입증계획 제시
- 스스로 약점 인정 (WeakPoints)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.legal.role_prompts import (
    LEGAL_STEERING_BLOCK,
    CLAIMANT_PROMPT,
    get_claimant_role_label,
    get_case_type_label,
)


class LegalAgentClaimant(BaseAgent):
    """검사/원고대리 (Claimant) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
        self._case_type = "civil"
        self._confirmed_facts = ""
        self._case_summary = ""
    
    @property
    def role_name(self) -> str:
        return "claimant"
    
    @property
    def system_prompt(self) -> str:
        # 템플릿 변수 치환
        prompt = CLAIMANT_PROMPT.replace("{{claimant_role}}", get_claimant_role_label(self._case_type))
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
        return {
            "type": "object",
            "properties": {
                "claims": {"type": "array", "items": {"type": "string"}},
                "legal_elements": {"type": "array", "items": {"type": "string"}},
                "evidence_plan": {"type": "array", "items": {"type": "string"}},
                "weak_points": {"type": "array", "items": {"type": "string"}, "maxItems": 2}
            }
        }
