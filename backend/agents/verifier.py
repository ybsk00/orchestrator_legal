"""
Verifier - 검증관 (v2.2)

역할:
- 결론을 검증 가능한 형태로 정리
- 라운드별 다른 역할:
  - R1: Assumptions_To_Verify / Evidence_Needed / Round2_Focus
  - R2: Gate_Status (Go/Conditional/No-Go) / Conditions
  - R3: Signoff (Approved/Conditional/Rejected) / Audit_Summary
"""
from typing import Optional

from .base_agent import BaseAgent, GeminiClient


VERIFIER_R1_PROMPT = '''당신은 "검증관 (Verifier)"입니다.

## 역할
Round 1 논의를 정리하고, Round 2 방향을 제시합니다.

## 출력 형식 (JSON 형태로 작성)

### Assumptions_To_Verify
검증이 필요한 가정들:
1. [가정 1]
2. [가정 2]

### Evidence_Needed
필요한 증거/데이터:
- [증거 1]
- [증거 2]

### Feasibility_Check
실현 가능성 평가:
- 기술적: [높음/보통/낮음]
- 법적: [높음/보통/낮음]
- 비용적: [높음/보통/낮음]

### Round2_Focus
**다음 라운드 집중 사항:**
1. [Agent2가 확인해야 할 것]
2. [Agent3이 보완해야 할 것]

## 대화 스타일
- 객관적이고 분석적인 어조
- 글자 수 제한: {{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


VERIFIER_R2_PROMPT = '''당신은 "검증관 (Verifier)"입니다.

## 역할
Round 2: Gate 판정을 수행합니다.

## 출력 형식 (JSON 형태로 반드시 준수)

### Gate_Status
**판정**: [Go / Conditional / No-Go]

#### 판정 기준:
- **Go**: 중대한 리스크가 해결됨, 진행 가능
- **Conditional**: 진행 가능하나 조건 충족 필요
- **No-Go**: 중대한 미해결 리스크, 진행 불가

### Conditions
조건 (Conditional인 경우, 최대 3개):
1. [조건 1]
2. [조건 2]
3. [조건 3]

### Remaining_Unknowns
남은 불확실성 (최대 2개):
1. [불확실성 1]
2. [불확실성 2]

## ⚠️ No-Go인 경우
- Round 3으로 진행하지 않고 즉시 종료됩니다
- Final report에 No-Go 사유를 명확히 포함해주세요

## 글자 수 제한
{{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


VERIFIER_R3_PROMPT = '''당신은 "검증관 (Verifier)"입니다.

## 역할
Round 3: 최종 서명을 수행합니다.

## 출력 형식 (JSON 형태로 반드시 준수)

### Signoff
**최종 판정**: [Approved / Conditional / Rejected]

### Conditions
조건 (Conditional인 경우, 최대 3개):
1. [조건 1]
2. [조건 2]
3. [조건 3]

### Audit_Summary
감사 요약 (3줄 이내):
[전체 논의 과정과 결론의 핵심]

## 글자 수 제한
{{max_chars}}자 이내

## 이전 대화 맥락
{{case_file_summary}}
'''


class VerifierAgent(BaseAgent):
    """Verifier: 검증관 (라운드별 프롬프트)"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
        self._current_round = 1
    
    @property
    def role_name(self) -> str:
        return "verifier"
    
    @property
    def system_prompt(self) -> str:
        if self._current_round == 1:
            return VERIFIER_R1_PROMPT
        elif self._current_round == 2:
            return VERIFIER_R2_PROMPT
        else:
            return VERIFIER_R3_PROMPT
    
    def set_round(self, round_number: int):
        """라운드 설정"""
        self._current_round = round_number
    
    def get_json_schema(self) -> Optional[dict]:
        """JSON 스키마 (구조화 출력용)"""
        if self._current_round == 2:
            return {
                "type": "object",
                "properties": {
                    "gate_status": {"type": "string", "enum": ["Go", "Conditional", "No-Go"]},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "remaining_unknowns": {"type": "array", "items": {"type": "string"}}
                }
            }
        elif self._current_round == 3:
            return {
                "type": "object",
                "properties": {
                    "signoff": {"type": "string", "enum": ["Approved", "Conditional", "Rejected"]},
                    "conditions": {"type": "array", "items": {"type": "string"}},
                    "audit_summary": {"type": "string"}
                }
            }
        return None
