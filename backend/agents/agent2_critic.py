"""
Agent2 - 리스크 오피서

역할:
- Agent1의 계획에서 허점/누락/병목 공격
- 치명 리스크 Top 3와 실패 시나리오 제시
- 반증 실험/확인 질문 2개 이상 제시
"""
from .base_agent import BaseAgent, GeminiClient


AGENT2_SYSTEM_PROMPT = '''당신은 "리스크 오피서 (Agent2)"입니다.

## 역할
- Agent1의 계획에서 허점/누락/병목/측정 불가능한 부분을 공격합니다.
- 치명 리스크 Top 3와 실패 시나리오를 제시합니다.
- 반증 실험/확인 질문을 반드시 2개 이상 제시합니다.

## 출력 형식
다음 구조로 응답하세요:

### 핵심 우려사항
(가장 중요한 우려 1~2문장)

### 리스크 분석
1. (치명 리스크 1)
2. (치명 리스크 2)
3. (치명 리스크 3)

### 실패 시나리오
- (실패 시나리오 1)
- (실패 시나리오 2)

### 검증 실험
- (제안하는 검증 실험 1)
- (제안하는 검증 실험 2)

### 확인 질문
- (Agent1에게 묻는 질문 1)
- (Agent1에게 묻는 질문 2)

## 이전 대화 맥락
{{case_file_summary}}
'''

AGENT2_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {
            "type": "string",
            "description": "핵심 우려사항 1~2문장"
        },
        "reasoning_summary": {
            "type": "array",
            "items": {"type": "string"},
            "description": "리스크 Top 3"
        },
        "failure_scenarios": {
            "type": "array",
            "items": {"type": "string"},
            "description": "실패 시나리오"
        },
        "verification_experiments": {
            "type": "array",
            "items": {"type": "string"},
            "description": "검증 실험"
        },
        "questions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "확인 질문"
        }
    },
    "required": ["conclusion", "reasoning_summary", "verification_experiments", "questions"]
}


class Agent2Critic(BaseAgent):
    """Agent2: 리스크 오피서"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "agent2"
    
    @property
    def system_prompt(self) -> str:
        return AGENT2_SYSTEM_PROMPT
    
    def get_json_schema(self) -> dict:
        return AGENT2_JSON_SCHEMA
