"""
Dev Project Agent: PRD Owner (Product Manager)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.devproject.role_prompts import (
    DEV_STEERING_BLOCK,
    PRD_R1_PROMPT,
    PRD_R2_PROMPT
)


class DevAgentPRD(BaseAgent):
    """PRD Owner (Product Manager) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
        self._topic = ""
    
    @property
    def role_name(self) -> str:
        return "prd"
    
    @property
    def system_prompt(self) -> str:
        # 라운드별 프롬프트 선택
        if self._current_round == 1:
            base_prompt = PRD_R1_PROMPT
        else:
            base_prompt = PRD_R2_PROMPT
        
        # Steering Block 주입 (BaseAgent에서 처리하지만, 여기서는 명시적으로 결합)
        # BaseAgent._build_prompt에서 steering_block을 최상단에 붙여주므로
        # 여기서는 플레이스홀더가 있다면 치환하고, 없다면 그대로 둠
        
        return base_prompt
    
    def set_round(self, round_number: int):
        """라운드 설정"""
        self._current_round = round_number
        
    def set_topic(self, topic: str):
        self._topic = topic
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        if self._current_round == 1:
            return {
                "type": "object",
                "properties": {
                    "core_features": {"type": "array", "items": {"type": "string"}},
                    "success_metrics": {"type": "array", "items": {"type": "string"}},
                    "target_users": {"type": "array", "items": {"type": "string"}},
                    "value_proposition": {"type": "string"}
                },
                "required": ["core_features", "success_metrics", "target_users", "value_proposition"]
            }
        else:
            return {
                "type": "object",
                "properties": {
                    "scope_adjustments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "feature": {"type": "string"},
                                "action": {"type": "string", "enum": ["keep", "drop", "modify"]},
                                "reason": {"type": "string"}
                            }
                        }
                    },
                    "finalized_features": {"type": "array", "items": {"type": "string"}},
                    "tradeoff_decisions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["scope_adjustments", "finalized_features", "tradeoff_decisions"]
            }
