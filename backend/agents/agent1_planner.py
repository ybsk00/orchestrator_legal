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

## 출력 형식
다음 구조로 응답하세요:

### 결론
(핵심 결론 1~2문장)

### 논리 요약
- (논리적 근거 1)
- (논리적 근거 2)
- (논리적 근거 3)

### 가정/제약
- (가정 또는 제약 조건)

### 다음 액션
- [ ] (실행 항목 1)
- [ ] (실행 항목 2)
- [ ] (실행 항목 3)

## 카테고리: {{category}}

## 루브릭
{{rubric}}

## 이전 대화 맥락
{{case_file_summary}}
'''

AGENT1_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {
            "type": "string",
            "description": "결론 1~2문장"
        },
        "reasoning_summary": {
            "type": "array",
            "items": {"type": "string"},
            "description": "논리 요약 3~6개 bullet"
        },
        "assumptions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "가정/제약"
        },
        "next_actions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "다음 액션 체크리스트"
        }
    },
    "required": ["conclusion", "reasoning_summary", "next_actions"]
}


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
        return AGENT1_JSON_SCHEMA
