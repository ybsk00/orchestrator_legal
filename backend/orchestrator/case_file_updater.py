"""
CaseFile 업데이트 - 라운드 종료 시 서버 주도 갱신

핵심 보완사항 반영:
- 라운드 종료 시점(A3_SYN_FINAL 후) 서버가 CaseFile 갱신
- 필수 필드 4종: decisions, open_issues, assumptions, next_experiments
- 길이 제한 적용
"""
from datetime import datetime
from typing import Optional

from models.case_file import CaseFile
from models.message import AgentResponse, Agent3Response


class CaseFileUpdater:
    """
    CaseFile 업데이트 관리자
    
    업데이트 시점: 라운드 종료 (A3_SYN_FINAL 완료 후)
    업데이트 방식: 서버 주도 (에이전트 응답 기반)
    """
    
    def update_on_round_end(
        self,
        case_file: CaseFile,
        agent3_response: Agent3Response
    ) -> CaseFile:
        """
        라운드 종료 시 CaseFile 갱신
        
        Args:
            case_file: 현재 CaseFile
            agent3_response: Agent3 최종 절충안 응답
            
        Returns:
            갱신된 CaseFile
        """
        # 결정사항 추가
        if agent3_response.conclusion:
            case_file.decisions.append(agent3_response.conclusion)
        
        # reasoning_summary에서 미해결/가정 분류
        for item in agent3_response.reasoning_summary:
            item_lower = item.lower()
            if any(kw in item_lower for kw in ["미해결", "추가 확인", "미정", "논의 필요"]):
                case_file.open_issues.append(item)
            elif any(kw in item_lower for kw in ["가정", "전제", "가설"]):
                case_file.assumptions.append(item)
        
        # 검증 플랜 추가
        if agent3_response.two_week_validation:
            case_file.next_experiments.extend(agent3_response.two_week_validation)
        
        # 길이 제한 적용
        case_file.trim_to_limits()
        
        return case_file
    
    def extract_facts_from_response(
        self,
        case_file: CaseFile,
        response: AgentResponse,
        agent_role: str
    ) -> CaseFile:
        """
        에이전트 응답에서 확정 사실 추출 (선택적)
        
        Args:
            case_file: 현재 CaseFile
            response: 에이전트 응답
            agent_role: 에이전트 역할 (agent1/agent2/agent3)
            
        Returns:
            갱신된 CaseFile
        """
        # 가정/제약 추가
        if response.assumptions:
            for assumption in response.assumptions:
                if assumption not in case_file.constraints:
                    case_file.constraints.append(assumption)
        
        case_file.trim_to_limits()
        return case_file


# 싱글톤 인스턴스
case_file_updater = CaseFileUpdater()
