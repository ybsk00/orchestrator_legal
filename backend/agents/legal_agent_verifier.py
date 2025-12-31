"""
법무 시뮬레이션 에이전트: 검증관 (Verifier)

역할:
- Gate 판정 (Go / Conditional / No-Go)
- Steering 준수 검사
- 환각/근거 없는 주장 감지
- 다음 라운드 집중 포인트 제시
"""
from typing import Optional

from agents.base_agent import BaseAgent, GeminiClient
from prompts.legal.role_prompts import (
    VERIFIER_LEGAL_PROMPT,
)


class LegalAgentVerifier(BaseAgent):
    """검증관 (Verifier) 에이전트"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
        self._case_summary = ""
    
    @property
    def role_name(self) -> str:
        return "verifier"
    
    @property
    def system_prompt(self) -> str:
        # 템플릿 변수 치환
        prompt = VERIFIER_LEGAL_PROMPT.replace("{{case_summary}}", self._case_summary or "없음")
        return prompt
    
    def set_round(self, round_number: int):
        """라운드 설정"""
        self._current_round = round_number
    
    def set_case_context(
        self, 
        case_type: str = "", 
        confirmed_facts: str = "", 
        case_summary: str = ""
    ):
        """사건 컨텍스트 설정"""
        self._case_summary = case_summary
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        return {
            "type": "object",
            "properties": {
                "gate_status": {
                    "type": "string",
                    "enum": ["Go", "Conditional", "No-Go"]
                },
                "steering_compliance": {
                    "type": "string",
                    "enum": ["OK", "NOT_OK"]
                },
                "unsupported_claims": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "missing_evidence": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "next_round_focus": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["gate_status", "steering_compliance"]
        }
    
    def extract_gate_status(self, response: str) -> str:
        """응답에서 Gate 상태 추출"""
        response_lower = response.lower()
        if "no-go" in response_lower or "no go" in response_lower:
            return "No-Go"
        elif "conditional" in response_lower:
            return "Conditional"
        elif "go" in response_lower:
            return "Go"
        return "Go"  # 기본값
    
    def extract_steering_compliance(self, response: str) -> str:
        """응답에서 Steering 준수 여부 추출"""
        response_lower = response.lower()
        if "not_ok" in response_lower or "not ok" in response_lower:
            return "NOT_OK"
        return "OK"
