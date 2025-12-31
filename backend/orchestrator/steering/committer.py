"""
Steering Committer
검증된 SteeringInput을 CaseFile에 반영하고, 프롬프트 주입용 블록을 생성합니다.
"""
import logging
from datetime import datetime
from typing import Optional

from orchestrator.steering.guard import SteeringResult, SteeringStatus
from storage.memory_store import memory_store
from models.case_file import CaseFile

logger = logging.getLogger(__name__)


async def commit_steering(session_id: str, result: SteeringResult) -> bool:
    """
    검증된 SteeringResult를 CaseFile에 저장합니다.
    """
    if result.status != SteeringStatus.COMMITTED:
        logger.warning(f"Cannot commit steering with status: {result.status}")
        return False
        
    case_file = memory_store.get_case_file(session_id)
    if not case_file:
        # CaseFile이 없으면 생성 (일반적으로는 이미 존재해야 함)
        logger.warning(f"CaseFile not found for session {session_id}, creating new one.")
        case_file = CaseFile(session_id=session_id)
        
    # 1. 히스토리 저장
    history_entry = {
        "raw_text": result.input_data.raw_text,
        "normalized": result.input_data.dict(),
        "status": result.status.value,
        "timestamp": datetime.utcnow().isoformat()
    }
    case_file.steering_history.append(history_entry)
    
    # 2. 스냅샷 업데이트 (최신 상태 반영)
    # 기존 스냅샷에 병합 (Changes는 누적하지 않고 이번 턴의 변경사항만 반영하는 것이 원칙이나,
    # 여기서는 스냅샷 자체가 '현재 유효한 설정'을 의미하므로 덮어쓰기/병합 로직이 중요)
    
    # Focus/Goal은 덮어쓰기
    current_snapshot = case_file.committed_steering_snapshot
    current_snapshot["focus"] = result.input_data.focus
    current_snapshot["goal"] = result.input_data.goal
    
    # Constraints는 병합 (중복 제거)
    existing_constraints = set(current_snapshot.get("constraints", []))
    new_constraints = set(result.input_data.constraints)
    current_snapshot["constraints"] = list(existing_constraints | new_constraints)
    
    # Changes는 이번 턴의 변경사항으로 기록 (누적하지 않음, 라운드별로 처리되므로)
    current_snapshot["changes"] = result.input_data.changes
    
    case_file.committed_steering_snapshot = current_snapshot
    
    # 저장
    memory_store.save_case_file(case_file)
    logger.info(f"Steering committed for session {session_id}")
    return True


def generate_steering_block(session_id: str) -> str:
    """
    에이전트 프롬프트에 주입할 Steering Block을 생성합니다.
    """
    case_file = memory_store.get_case_file(session_id)
    if not case_file or not case_file.committed_steering_snapshot:
        return ""
        
    snapshot = case_file.committed_steering_snapshot
    
    focus = snapshot.get("focus", "General")
    goal = snapshot.get("goal", "Quality")
    constraints = snapshot.get("constraints", [])
    changes = snapshot.get("changes", [])
    
    block = f"""
[STEERING — MUST FOLLOW]
Focus: {focus}
Goal: {goal}
Constraints: {', '.join(constraints) if constraints else 'None'}
ApprovedChanges: {', '.join(changes) if changes else 'None'}

RULES:
1. Focus 범위를 벗어난 논점 확장 금지
2. Goal/Constraints를 최우선 반영
3. ApprovedChanges 외 신규 기능 제안 금지
4. 답변 끝에 'Steering Compliance Check: OK/NOT_OK' 포함
"""
    return block.strip()
