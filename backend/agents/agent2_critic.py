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

## 대화 스타일 (중요)
- 상대방과 대화하듯이 자연스러운 구어체를 사용하세요. ("~합니다" 대신 "~해요", "~인가요?" 등)
- 장황한 독백보다는 핵심 위주로 명확하게 전달하세요.
- 주어진 글자 수 제한을 엄격히 준수하세요.

## 현재 턴 지시사항
{{turn_instruction}}

## 글자 수 제한
{{max_chars}}자 이내로 작성하세요.

## 이전 대화 맥락
{{case_file_summary}}
'''

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
        return None  # 대화형 모드에서는 JSON 스키마 사용 안 함
