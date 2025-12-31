"""
Dev Project Agent: Delivery Manager (Agile Coach)
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.devproject.role_prompts import (
    DEV_STEERING_BLOCK,
    DM_R1_PROMPT,
    DM_R2_PROMPT,
    DM_R3_PROMPT
)


class DevAgentDM(BaseAgent):
    """Delivery Manager (Agile Coach) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
    
    @property
    def role_name(self) -> str:
        return "dm"
    
    @property
    def system_prompt(self) -> str:
        if self._current_round == 1:
            return DM_R1_PROMPT
        elif self._current_round == 2:
            return DM_R2_PROMPT
        else:
            return DM_R3_PROMPT
    
    def set_round(self, round_number: int):
        self._current_round = round_number
        
    def get_json_schema(self) -> Optional[dict]:
        if self._current_round == 1:
            return {
                "type": "object",
                "properties": {
                    "estimated_timeline": {"type": "string"},
                    "resource_needs": {"type": "array", "items": {"type": "string"}},
                    "potential_blockers": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["estimated_timeline", "resource_needs", "potential_blockers"]
            }
        elif self._current_round == 2:
            return {
                "type": "object",
                "properties": {
                    "milestones": {"type": "array", "items": {"type": "string"}},
                    "dependencies": {"type": "array", "items": {"type": "string"}},
                    "action_items": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["milestones", "dependencies", "action_items"]
            }
        else:
            return {
                "type": "object",
                "properties": {
                    "final_summary": {"type": "string"},
                    "key_decisions": {"type": "array", "items": {"type": "string"}},
                    "next_steps": {"type": "array", "items": {"type": "string"}},
                    "sign_off_request": {"type": "string"}
                },
                "required": ["final_summary", "key_decisions", "next_steps", "sign_off_request"]
            }
