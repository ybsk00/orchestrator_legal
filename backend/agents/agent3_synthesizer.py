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

## 출력 형식
다음 구조로 응답하세요:

### 절충안 요약
(핵심 절충안 1~2문장)

### 판단 근거
- (근거 1)
- (근거 2)
- (근거 3)

### Agent2 지적 대응
| 지적사항 | 대응 | 조치 |
|---------|-----|------|
| (지적 1) | 수용/보류/반박 | (조치 내용) |
| (지적 2) | 수용/보류/반박 | (조치 내용) |

### 개선된 실행안
(구체적인 개선 계획)

### Plan B
(대안 계획)

### 2주 검증 플랜
- [ ] (검증 항목 1)
- [ ] (검증 항목 2)

## 이전 대화 맥락
{{case_file_summary}}
'''

AGENT3_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "conclusion": {
            "type": "string",
            "description": "절충안 핵심 1~2문장"
        },
        "reasoning_summary": {
            "type": "array",
            "items": {"type": "string"},
            "description": "판단 근거"
        },
        "critique_responses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "critique": {"type": "string"},
                    "response_type": {"type": "string", "enum": ["수용", "보류", "반박"]},
                    "action": {"type": "string"}
                }
            },
            "description": "지적 대응"
        },
        "improved_plan": {
            "type": "string",
            "description": "개선된 실행안"
        },
        "plan_b": {
            "type": "string",
            "description": "대안"
        },
        "two_week_validation": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2주 검증 플랜"
        }
    },
    "required": ["conclusion", "reasoning_summary", "improved_plan", "two_week_validation"]
}


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
        return AGENT3_JSON_SCHEMA
