"""
Agent1 - 구현계획 전문가 (v2.2)

역할:
- Round 1에서만 호출 (Round 2/3에서 호출 금지!)
- MVP/일정/KPI를 포함한 초기 구현 계획 제시
- 출력 스키마 고정
"""
from typing import Optional

from .base_agent import BaseAgent, GeminiClient


# Round 1 전용 프롬프트
AGENT1_R1_PROMPT = '''당신은 "구현계획 전문가 (Agent1)"입니다.

## 역할
사용자의 주제에 대해 구체적인 실행계획/구현방안을 제시합니다.

## ⚠️ 중요: 이 프롬프트는 Round 1에서만 사용됩니다
Round 2/3에서는 Agent1이 호출되지 않습니다.

## 출력 형식 (반드시 준수)

### MVP_Scope
- [핵심 기능 1]
- [핵심 기능 2]
- [핵심 기능 3]

### Milestones
1. [1단계]: [기간]
2. [2단계]: [기간]
3. [3단계]: [기간]

### Resources
- 역할: [필요 인력]
- 툴: [필요 도구]
- 예산: [예상 비용]

### KPI
- [KPI 1]: [측정 방법]
- [KPI 2]: [측정 방법]
- [KPI 3]: [측정 방법]

### Open_Assumptions
- [검증이 필요한 가정 1]
- [검증이 필요한 가정 2]

## 대화 스타일
- 자연스러운 구어체 ("~해요", "~인가요?")
- 핵심 위주로 명확하게
- 글자 수 제한: {{max_chars}}자 이내

## 주제
{{topic}}

## 카테고리
{{category}}
'''


class Agent1Planner(BaseAgent):
    """Agent1: 구현계획 전문가 (Round 1 전용)"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "agent1"
    
    @property
    def system_prompt(self) -> str:
        return AGENT1_R1_PROMPT
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        return {
            "type": "object",
            "properties": {
                "mvp_scope": {"type": "array", "items": {"type": "string"}},
                "milestones": {"type": "array", "items": {"type": "string"}},
                "resources": {"type": "object"},
                "kpi": {"type": "array", "items": {"type": "object"}},
                "open_assumptions": {"type": "array", "items": {"type": "string"}}
            }
        }
