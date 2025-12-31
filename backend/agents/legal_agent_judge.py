"""
법무 시뮬레이션 에이전트: 재판장 (Judge)

역할:
- R1: 프레임 설정 (Issue_Candidates, Missing_Facts_Questions, Burden_Of_Proof_Map) - 판단 금지!
- R2: 쟁점 정리, 입증책임 확정
- R3: 판단 범위, 권고안 제시
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.legal.role_prompts import (
    LEGAL_STEERING_BLOCK,
    JUDGE_R1_FRAME_PROMPT,
    JUDGE_R2_PROMPT,
    JUDGE_R3_PROMPT,
    get_case_type_label,
)


class LegalAgentJudge(BaseAgent):
    """재판장 (Judge) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
        self._case_type = "civil"  # 기본값
        self._confirmed_facts = ""
        self._case_summary = ""
    
    @property
    def role_name(self) -> str:
        return "judge"
    
    @property
    def system_prompt(self) -> str:
        # 라운드별 프롬프트 선택
        if self._current_round == 1:
            base_prompt = JUDGE_R1_FRAME_PROMPT
        elif self._current_round == 2:
            base_prompt = JUDGE_R2_PROMPT
        else:
            base_prompt = JUDGE_R3_PROMPT
        
        # 템플릿 변수 치환
        prompt = base_prompt.replace("{{case_type_label}}", get_case_type_label(self._case_type))
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
        if self._current_round == 1:
            # R1: 프레임만
            return {
                "type": "object",
                "properties": {
                    "issue_candidates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 5
                    },
                    "missing_facts_questions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 5
                    },
                    "burden_of_proof_map": {
                        "type": "object"
                    }
                }
            }
        else:
            # R2/R3: 전체 스키마
            return {
                "type": "object",
                "properties": {
                    "issues": {"type": "array", "items": {"type": "string"}},
                    "findings": {"type": "array", "items": {"type": "string"}},
                    "burden_of_proof": {"type": "string"},
                    "decision_range": {"type": "string"},
                    "recommended_next_steps": {"type": "array", "items": {"type": "string"}},
                    "citations": {"type": "array", "items": {"type": "string"}}
                }
            }
