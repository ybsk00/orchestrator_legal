"""
Dev Project Agent: UX Lead (Designer)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.devproject.role_prompts import (
    DEV_STEERING_BLOCK,
    UX_R1_PROMPT,
    UX_R2_PROMPT,
    UX_R3_PROMPT
)


class DevAgentUX(BaseAgent):
    """UX Lead (Designer) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
    
    @property
    def role_name(self) -> str:
        return "ux"
    
    @property
    def system_prompt(self) -> str:
        if self._current_round == 1:
            return UX_R1_PROMPT
        elif self._current_round == 2:
            return UX_R2_PROMPT
        else:
            return UX_R3_PROMPT
    
    def set_round(self, round_number: int):
        self._current_round = round_number
        
    def get_json_schema(self) -> Optional[dict]:
        if self._current_round == 1:
            return {
                "type": "object",
                "properties": {
                    "user_journey_steps": {"type": "array", "items": {"type": "string"}},
                    "ux_pain_points": {"type": "array", "items": {"type": "string"}},
                    "key_interactions": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["user_journey_steps", "ux_pain_points", "key_interactions"]
            }
        elif self._current_round == 2:
            return {
                "type": "object",
                "properties": {
                    "edge_cases": {"type": "array", "items": {"type": "string"}},
                    "ui_components": {"type": "array", "items": {"type": "string"}},
                    "usability_improvements": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["edge_cases", "ui_components", "usability_improvements"]
            }
        else:
            return {
                "type": "object",
                "properties": {
                    "ux_sign_off": {"type": "string", "enum": ["Approved", "Conditional", "Rejected"]},
                    "final_remarks": {"type": "string"}
                },
                "required": ["ux_sign_off", "final_remarks"]
            }
