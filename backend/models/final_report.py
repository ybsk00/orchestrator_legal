"""
최종 리포트 모델
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RoadmapItem(BaseModel):
    """실행 로드맵 항목"""
    week: str  # "1주차", "2주차" 등
    tasks: List[str]


class RiskItem(BaseModel):
    """리스크 항목"""
    risk: str
    mitigation: str


class FinalReport(BaseModel):
    """
    최종 결과물 JSON 스키마 (렌더링 목적)
    Agent3 Finalizer가 생성
    """
    session_id: str
    category: str
    
    # 필수 섹션
    executive_summary: str  # 최종 결론 (5~8줄)
    top_decisions: List[str]  # 채택된 방향 Top 5
    roadmap: List[RoadmapItem]  # 실행 로드맵 (주차별)
    risks: List[RiskItem]  # 리스크 및 대응 Top 5
    kpis: List[str]  # KPI/측정 (판정 기준 포함)
    open_issues: List[str]  # 오픈 이슈
    
    # 선택 섹션
    round_summaries: Optional[List[str]] = None  # 라운드별 결정 요약
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
