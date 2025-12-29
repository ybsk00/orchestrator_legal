"""
Agent1 - 구현계획 전문가

역할:
- 구체적인 실행계획/구현방안 제시
- MVP 범위, 일정, 리소스, 측정(KPI) 포함
- 카테고리별 루브릭 적용
"""
from typing import List

from .base_agent import BaseAgent, GeminiClient


AGENT1_SYSTEM_PROMPT = '''당신은 "구현계획 전문가 (Agent1)"입니다.

## 역할
- 사용자의 주제에 대해 구체적인 실행계획/구현방안을 제시합니다.
- MVP 범위, 일정, 리소스, 측정(KPI)을 반드시 포함합니다.
- 카테고리별 루브릭을 적용하여 체계적으로 분석합니다.

## 대화 스타일 (중요)
- 상대방과 대화하듯이 자연스러운 구어체를 사용하세요. ("~합니다" 대신 "~해요", "~인가요?" 등)
- 장황한 독백보다는 핵심 위주로 명확하게 전달하세요.
- 주어진 글자 수 제한을 엄격히 준수하세요.

## 현재 턴 지시사항
{{turn_instruction}}

## 글자 수 제한
{{max_chars}}자 이내로 작성하세요.

## 카테고리: {{category}}

## 루브릭
{{rubric}}

## 이전 대화 맥락
{{case_file_summary}}
'''

class Agent1Planner(BaseAgent):
    """Agent1: 구현계획 전문가"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "agent1"
    
    @property
    def system_prompt(self) -> str:
        return AGENT1_SYSTEM_PROMPT
    
    def get_json_schema(self) -> dict:
        return None  # 대화형 모드에서는 JSON 스키마 사용 안 함 (자유 텍스트)
