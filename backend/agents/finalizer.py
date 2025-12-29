"""
Finalizer - Agent3 최종안 생성기

역할:
- 토론 종료 시 최종 결과물 생성
- 결론, 로드맵, 리스크, KPI, 오픈 이슈 포함
"""
from typing import Optional

from .base_agent import BaseAgent, GeminiClient
from models.final_report import FinalReport


FINALIZER_SYSTEM_PROMPT = '''당신은 "최종안 생성자 (Finalizer)"입니다.

## 역할
지금까지의 토론 내용을 종합하여 최종 결과물을 생성합니다.

## 출력 형식
다음 구조로 최종 결과물을 작성하세요:

### 최종 결론 (Executive Summary)
(5~8줄의 종합 결론)

### 채택된 방향 (Top 5)
1. (결정사항 1)
2. (결정사항 2)
3. (결정사항 3)
4. (결정사항 4)
5. (결정사항 5)

### 실행 로드맵
#### 1주차
- (실행 항목)

#### 2주차
- (실행 항목)

### 리스크 및 대응
| 리스크 | 대응 방안 |
|-------|----------|
| (리스크 1) | (대응 1) |

### KPI/측정
- (측정 지표 1)
- (측정 지표 2)

### 오픈 이슈
- (미해결 사항)

## 토론 맥락
{{case_file_summary}}

## 카테고리: {{category}}
'''

FINALIZER_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "executive_summary": {
            "type": "string",
            "description": "최종 결론 (5~8줄)"
        },
        "top_decisions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "채택된 방향 Top 5"
        },
        "roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "week": {"type": "string"},
                    "tasks": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },
            "description": "실행 로드맵"
        },
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "risk": {"type": "string"},
                    "mitigation": {"type": "string"}
                }
            },
            "description": "리스크 및 대응"
        },
        "kpis": {
            "type": "array",
            "items": {"type": "string"},
            "description": "KPI/측정"
        },
        "open_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "오픈 이슈"
        }
    },
    "required": ["executive_summary", "top_decisions", "roadmap", "risks", "kpis", "open_issues"]
}


class Finalizer(BaseAgent):
    """Finalizer: 최종안 생성기"""
    
    def __init__(self, gemini_client: GeminiClient):
        super().__init__(gemini_client)
    
    @property
    def role_name(self) -> str:
        return "finalizer"
    
    @property
    def system_prompt(self) -> str:
        return FINALIZER_SYSTEM_PROMPT
    
    def get_json_schema(self) -> dict:
        return FINALIZER_JSON_SCHEMA
    
    async def generate_final_report(
        self,
        session_id: str,
        category: str,
        case_file_summary: str,
        round_summaries: Optional[list] = None
    ) -> FinalReport:
        """
        최종 리포트 생성
        
        Args:
            session_id: 세션 ID
            category: 카테고리
            case_file_summary: CaseFile 요약
            round_summaries: 라운드별 요약 (선택)
            
        Returns:
            FinalReport 인스턴스
        """
        # 스트리밍으로 응답 생성
        full_text = ""
        async for chunk in self.stream_response(
            messages=[],
            user_message="지금까지의 토론을 종합하여 최종 결과물을 생성해주세요.",
            case_file_summary=case_file_summary,
            category=category
        ):
            full_text += chunk
        
        # JSON 구조화
        json_data = await self.get_structured_response()
        
        if "error" in json_data:
            # 에러 시 기본값 반환
            return FinalReport(
                session_id=session_id,
                category=category,
                executive_summary=full_text[:500] if full_text else "최종안 생성 실패",
                top_decisions=[],
                roadmap=[],
                risks=[],
                kpis=[],
                open_issues=["최종안 생성 중 오류 발생"],
                round_summaries=round_summaries
            )
        
        return FinalReport(
            session_id=session_id,
            category=category,
            executive_summary=json_data.get("executive_summary", ""),
            top_decisions=json_data.get("top_decisions", []),
            roadmap=[
                {"week": item.get("week", ""), "tasks": item.get("tasks", [])}
                for item in json_data.get("roadmap", [])
            ],
            risks=[
                {"risk": item.get("risk", ""), "mitigation": item.get("mitigation", "")}
                for item in json_data.get("risks", [])
            ],
            kpis=json_data.get("kpis", []),
            open_issues=json_data.get("open_issues", []),
            round_summaries=round_summaries
        )
