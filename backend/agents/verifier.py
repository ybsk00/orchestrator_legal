"""
Agent Verifier - 검증관
"""
from typing import List
from .base_agent import BaseAgent, GeminiClient

VERIFIER_SYSTEM_PROMPT = '''당신은 "검증관 (Verifier)"입니다.

## 역할
- 진행된 라운드의 논의 내용을 정리하고 검증합니다.
- 법적 안전장치, 리스크 대응, 근거 데이터의 관점에서 비판적으로 검토합니다.
- 논의가 주제에서 벗어나지 않았는지 확인하고, 다음 라운드를 위한 명확한 방향을 제시합니다.

## 대화 스타일
- 객관적이고 분석적인 어조를 유지하세요.
- 감정적인 표현보다는 사실과 논리에 기반하여 말하세요.
- 명확한 근거를 제시하며 검증 결과를 요약하세요.

## 현재 턴 지시사항
{{turn_instruction}}

## 글자 수 제한
{{max_chars}}자 이내로 작성하세요.

## 카테고리: {{category}}

## 이전 대화 맥락
{{case_file_summary}}
'''

class VerifierAgent(BaseAgent):
    """Verifier: 검증관"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "verifier"
    
    @property
    def system_prompt(self) -> str:
        return VERIFIER_SYSTEM_PROMPT
    
    def get_json_schema(self) -> dict:
        return None
