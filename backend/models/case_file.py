"""
CaseFile 모델 - 누적 메모리 (세션 컨텍스트)
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import CASEFILE_MAX_CHARS


class CaseFile(BaseModel):
    """
    누적 메모리 (세션 컨텍스트)
    
    라운드 종료 시점(A3_SYN_FINAL 후) 서버가 갱신
    다음 라운드 프롬프트 및 최종안 생성의 핵심 입력
    """
    session_id: str
    facts: List[str] = Field(default_factory=list, description="확정 사실")
    goals: List[str] = Field(default_factory=list, description="KPI/우선순위")
    constraints: List[str] = Field(default_factory=list, description="예산/기간/리소스/금지")
    decisions: List[str] = Field(default_factory=list, description="합의된 결론")
    open_issues: List[str] = Field(default_factory=list, description="미해결 쟁점")
    assumptions: List[str] = Field(default_factory=list, description="가정")
    next_experiments: List[str] = Field(default_factory=list, description="검증 실험")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 법무 시뮬레이션 전용 필드 - Facts Stipulation
    confirmed_facts: List[str] = Field(default_factory=list, description="확정된 사실 (증거/합의)")
    disputed_facts: List[str] = Field(default_factory=list, description="다툼/쟁점 사실")
    missing_facts_questions: List[str] = Field(default_factory=list, description="누락 사실 질문")
    case_overview: Optional[str] = Field(default=None, description="사건 개요")
    parties: List[str] = Field(default_factory=list, description="당사자")
    
    # 법무 시뮬레이션 전용 필드 - Legal Steering (USER_GATE 입력)
    legal_steering: Optional[Dict[str, Any]] = Field(default=None, description="법무 Steering 데이터")
    # 예: {focus_issue, goal, constraints, stance, exclusions, notes, proof_priority, evidence_level}
    
    # 이전 라운드 비판 태그 (기존 호환)
    criticisms_so_far: List[str] = Field(default_factory=list)
    criticisms_last_round: List[str] = Field(default_factory=list)
    
    def get_summary(self, max_chars: int = CASEFILE_MAX_CHARS) -> str:
        """
        CaseFile 요약 (권장 800~1200자)
        다음 라운드 프롬프트 및 최종안 생성의 핵심 입력
        """
        summary_parts = []
        
        if self.decisions:
            summary_parts.append(f"[결정사항] {'; '.join(self.decisions[-3:])}")
        if self.open_issues:
            summary_parts.append(f"[미해결] {'; '.join(self.open_issues[-3:])}")
        if self.assumptions:
            summary_parts.append(f"[가정] {'; '.join(self.assumptions[-2:])}")
        if self.next_experiments:
            summary_parts.append(f"[검증계획] {'; '.join(self.next_experiments[-2:])}")
        if self.goals:
            summary_parts.append(f"[목표] {'; '.join(self.goals[-2:])}")
        if self.constraints:
            summary_parts.append(f"[제약] {'; '.join(self.constraints[-2:])}")
        
        summary = " | ".join(summary_parts)
        return summary[:max_chars] if len(summary) > max_chars else summary
    
    def trim_to_limits(self):
        """길이 제한 적용 (오래된 항목 제거)"""
        self.decisions = self.decisions[-10:]
        self.open_issues = self.open_issues[-5:]
        self.assumptions = self.assumptions[-5:]
        self.next_experiments = self.next_experiments[-5:]
        self.facts = self.facts[-10:]
        self.goals = self.goals[-5:]
        self.constraints = self.constraints[-5:]
        self.updated_at = datetime.utcnow()
