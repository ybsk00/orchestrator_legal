"""
Agent2 - 리스크 오피서 (v2.2)

역할:
- Agent1/Agent3의 산출물에서 리스크 비판
- 라운드별 다른 역할:
  - R1: 초안의 치명 리스크 Top 3
  - R2: 새로운/남은 리스크만 (기존 반복 금지)
  - R3: 최종 경고 1~2개만
- 표준 태그로 리스크 분류
"""
from typing import Optional

from .base_agent import BaseAgent, GeminiClient


# 표준 리스크 태그 (Controlled Vocabulary)
RISK_TAGS = [
    "compliance",      # 법적/규제 리스크
    "security",        # 보안 리스크
    "data_quality",    # 데이터 품질
    "cost",            # 비용 리스크
    "timeline",        # 일정 리스크
    "ux",              # 사용자 경험
    "ops",             # 운영 리스크
    "deliverability",  # 전달 가능성
    "tracking",        # 추적/측정
    "integration",     # 통합 리스크
]


# 라운드별 프롬프트
AGENT2_R1_PROMPT = '''당신은 "리스크 오피서 (Agent2)"입니다.

## 역할
Agent1의 초기 계획에서 허점/리스크를 비판합니다.

## 출력 형식 (반드시 준수)

### Top_Risks
각 리스크에 [태그]를 반드시 포함하세요.
태그 목록: compliance, security, data_quality, cost, timeline, ux, ops, deliverability, tracking, integration

1. [태그] 리스크 제목
   - 상세 설명

2. [태그] 리스크 제목
   - 상세 설명

3. [태그] 리스크 제목
   - 상세 설명

### Failure_Scenario
[이 계획이 실패할 경우 구체적인 시나리오]

### Disproof_Questions
1. [검증 질문 1]
2. [검증 질문 2]

## 대화 스타일
- 핵심 위주로 명확하게
- 글자 수 제한: {{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


AGENT2_R2_PROMPT = '''당신은 "리스크 오피서 (Agent2)"입니다.

## 역할
Round 2: 새로운/남은 리스크만 지적합니다.

## ⛔ 중요: 반복 금지
이전 라운드에서 지적한 리스크: {{criticisms_last_round}}
위 리스크를 그대로 반복하지 마세요. **새로운 리스크** 또는 **해결되지 않은 리스크**만 제시하세요.

## 출력 형식 (반드시 준수)

### Top_Risks (새로운 것만!)
태그 목록: compliance, security, data_quality, cost, timeline, ux, ops, deliverability, tracking, integration

1. [태그] 리스크 제목
   - 상세 설명

2. [태그] 리스크 제목 (선택)
   - 상세 설명

### Failure_Scenario
[실패 시나리오]

### Disproof_Questions
1. [질문 1]
2. [질문 2]

## 글자 수 제한
{{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


AGENT2_R3_PROMPT = '''당신은 "리스크 오피서 (Agent2)"입니다.

## 역할
Round 3: 최종 경고 1~2개만 간결하게 제시합니다.

## ⛔ 중요
- 이미 논의된 내용을 길게 반복하지 마세요
- 절대적으로 중요한 경고만 1~2개 제시

## 출력 형식 (반드시 준수)

### Final_Warnings
1. [태그] 마지막 경고
   - 간단한 설명

2. [태그] 마지막 경고 (선택)
   - 간단한 설명

## 글자 수 제한
{{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


class Agent2Critic(BaseAgent):
    """Agent2: 리스크 오피서 (라운드별 프롬프트)"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
    
    @property
    def role_name(self) -> str:
        return "agent2"
    
    @property
    def system_prompt(self) -> str:
        if self._current_round == 1:
            return AGENT2_R1_PROMPT
        elif self._current_round == 2:
            return AGENT2_R2_PROMPT
        else:
            return AGENT2_R3_PROMPT
    
    def set_round(self, round_number: int):
        """라운드 설정"""
        self._current_round = round_number
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        return {
            "type": "object",
            "properties": {
                "top_risks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tag": {"type": "string"},
                            "title": {"type": "string"},
                            "detail": {"type": "string"}
                        }
                    }
                },
                "failure_scenario": {"type": "string"},
                "disproof_questions": {"type": "array", "items": {"type": "string"}}
            }
        }
