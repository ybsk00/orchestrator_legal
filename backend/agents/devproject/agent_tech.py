"""
Dev Project Agent: Tech Lead (CTO)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.devproject.role_prompts import (
    DEV_STEERING_BLOCK,
    TECH_R1_PROMPT,
    TECH_R2_PROMPT,
    TECH_R3_PROMPT
)


class DevAgentTech(BaseAgent):
    """Tech Lead (CTO) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
    
    @property
    def role_name(self) -> str:
        return "tech"
    
    @property
    def system_prompt(self) -> str:
        if self._current_round == 1:
            return TECH_R1_PROMPT
        elif self._current_round == 2:
            return TECH_R2_PROMPT
        else:
            return TECH_R3_PROMPT # R3는 DM 주도지만 Tech도 참여 가능 (현재 프롬프트에는 R3 정의 안됨, 필요시 추가)
            # role_prompts.py에 TECH_R3_PROMPT가 없으므로 TECH_R2_PROMPT 재사용하거나 추가 필요
            # 일단 R2 사용 (R3는 DM이 메인)
            return TECH_R2_PROMPT
    
    def set_round(self, round_number: int):
        self._current_round = round_number
        
    def get_json_schema(self) -> Optional[dict]:
        if self._current_round == 1:
            return {
                "type": "object",
                "properties": {
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                    "feasibility_issues": {"type": "array", "items": {"type": "string"}},
                    "architecture_suggestion": {"type": "string"},
                    "estimated_complexity": {"type": "string", "enum": ["High", "Medium", "Low"]}
                },
                "required": ["tech_stack", "feasibility_issues", "architecture_suggestion", "estimated_complexity"]
            }
        else:
            return {
                "type": "object",
                "properties": {
                    "critical_risks": {"type": "array", "items": {"type": "string"}},
                    "mitigation_plans": {"type": "array", "items": {"type": "string"}},
                    "development_roadmap": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["critical_risks", "mitigation_plans", "development_roadmap"]
            }
