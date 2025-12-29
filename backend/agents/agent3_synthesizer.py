"""
Agent3 - 합의안 설계자

역할:
- Agent1의 계획과 Agent2의 반박을 종합
- 각 지적사항을 "수용/보류/반박"으로 분류
- 개선된 실행안, Plan B, 2주 검증 플랜 포함
"""
from .base_agent import BaseAgent, GeminiClient


AGENT3_SYSTEM_PROMPT = '''당신은 "합의안 설계자 (Agent3)"입니다.

## 역할
- Agent1의 계획과 Agent2의 반박을 종합하여 절충안을 제시합니다.
- 각 지적사항을 "수용/보류/반박"으로 분류합니다.
- 개선된 실행안, Plan B, 2주 검증 플랜을 포함합니다.

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

class Agent3Synthesizer(BaseAgent):
    """Agent3: 합의안 설계자"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "agent3"
    
    @property
    def system_prompt(self) -> str:
        return AGENT3_SYSTEM_PROMPT
    
    def get_json_schema(self) -> dict:
        return None  # 대화형 모드에서는 JSON 스키마 사용 안 함
