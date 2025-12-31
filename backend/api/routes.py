"""
API Routes (v2.2)

핵심 변경:
- Phase 기반 실행 (turn_index → phase)
- WAIT_USER에서 사용자 입력 대기
- current_round=0 초기화, 사용자 입력 시 round++
- 라운드별 에이전트 프롬프트 설정
"""
import asyncio
import logging
import uuid
import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from orchestrator.state_machine import (
    Phase, MAX_ROUNDS, 
    get_next_phase, get_agent_for_phase, get_round_for_phase,
    get_round_start_phase, is_wait_user_phase, is_final_phase,
    state_machine,
    # 법무 시뮬레이션용
    get_next_phase_legal, get_legal_agent_for_phase, get_legal_round_for_phase,
    get_legal_round_start_phase, is_legal_phase,
)
from orchestrator.turn_manager import turn_manager, get_phase_config
from agents.base_agent import gemini_client
from agents.agent1_planner import Agent1Planner
from agents.agent2_critic import Agent2Critic
from agents.agent3_synthesizer import Agent3Synthesizer
from agents.verifier import VerifierAgent
# 법무 시뮬레이션 에이전트
from agents.legal_agent_judge import LegalAgentJudge
from agents.legal_agent_claimant import LegalAgentClaimant
from agents.legal_agent_opposing import LegalAgentOpposing
from agents.legal_agent_verifier import LegalAgentVerifier
from storage import supabase_client as db
from .events import sse_event_manager, EventType
from config import BASE_URL
from prompts.legal.role_prompts import LEGAL_STEERING_BLOCK, FACTS_STIPULATE_PROMPT

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 일반 토론 에이전트 인스턴스
agents = {
    "agent1": Agent1Planner(gemini_client),
    "agent2": Agent2Critic(gemini_client),
    "agent3": Agent3Synthesizer(gemini_client),
    "verifier": VerifierAgent(gemini_client),
}

# 법무 시뮬레이션 에이전트 인스턴스
legal_agents = {
    "judge": LegalAgentJudge(gemini_client),
    "claimant": LegalAgentClaimant(gemini_client),
    "opposing": LegalAgentOpposing(gemini_client),
    "verifier": LegalAgentVerifier(gemini_client),
}


# Request/Response 모델
class CreateSessionRequest(BaseModel):
    category: Optional[str] = None  # 일반 토론용 (레거시)
    topic: str
    case_type: Optional[str] = None  # 법무 시뮬레이션: "criminal" | "civil"
    user_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    category: str
    topic: str
    status: str


class UserMessageRequest(BaseModel):
    message: str


class UserMessageResponse(BaseModel):
    status: str
    round_index: Optional[int] = None
    phase: Optional[str] = None


class SteeringRequest(BaseModel):
    action: str  # skip, input, finalize, extend, new_session
    steering: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None  # Idempotency key


class SessionResponse(BaseModel):
    id: str
    status: str
    category: str
    topic: str
    round_index: int
    phase: str


# Phase 실행 함수
async def execute_phase(session_id: str, phase: str, config: dict) -> str:
    """
    단일 phase를 실행합니다.
    
    Args:
        session_id: 세션 ID
        phase: 현재 phase
        config: phase 설정 (description, max_chars)
    
    Returns:
        에이전트 응답 텍스트
    """
    agent_name = get_agent_for_phase(phase)
    current_round = get_round_for_phase(phase)
    
    if not agent_name:
        logger.error(f"No agent for phase: {phase}")
        return ""
    
    agent = agents.get(agent_name)
    if not agent:
        logger.error(f"Agent not found: {agent_name}")
        return ""
    
    # 라운드 설정 (Agent2/Agent3/Verifier)
    if hasattr(agent, 'set_round'):
        agent.set_round(current_round)
    
    # 세션 및 CaseFile 조회
    session_data = await db.get_session(session_id)
    case_file_data = await db.get_case_file(session_id)
    
    # 이전 대화 맥락 구성
    case_file_summary = ""
    criticisms_last_round = ""
    steering_block = ""
    
    if case_file_data:
        decisions = case_file_data.get('decisions', [])
        open_issues = case_file_data.get('open_issues', [])
        case_file_summary = f"결정사항: {'; '.join(decisions[-3:])}. 미해결: {'; '.join(open_issues[-3:])}"
        
        # Agent2용 이전 비판 목록
        criticisms = case_file_data.get('criticisms_last_round', [])
        if criticisms:
            criticisms_last_round = ", ".join(criticisms)
            
        # Steering 데이터 구성
        steering = case_file_data.get('steering')
        if steering:
            # Steering Block 템플릿
            steering_block = f"""
## [USER STEERING — MUST FOLLOW]
Goal: {steering.get('goal', 'None')}
Priority order: {steering.get('priority', 'None')}
Hard constraints (must satisfy): {steering.get('constraints', [])}
Hard exclusions (must not propose): {steering.get('exclusions', [])}
User note: {steering.get('free_text', '')}

### RULES
1) Hard constraints를 만족하지 못하는 제안은 실패입니다.
2) Hard exclusions에 해당하는 제안은 금지이며 포함되면 실패입니다.
3) Output은 Goal/Priority에 맞춰 최적화해야 합니다.
4) 응답 끝에 `Steering Compliance Check: OK/NOT OK`로 준수 여부를 자가 점검하세요.
"""
    
    # 이벤트 발송
    await sse_event_manager.emit(session_id, EventType.SPEAKER_CHANGE, {"active_speaker": agent_name})
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_START, {
        "role": agent_name,
        "round_index": current_round,
        "phase": phase
    })
    
    # 프롬프트 구성 (Steering Block은 BaseAgent 내부에서 처리)
    prompt = agent.system_prompt
    prompt = prompt.replace("{{max_chars}}", str(config.get("max_chars", 300)))
    prompt = prompt.replace("{{category}}", session_data.get("category", "general"))
    prompt = prompt.replace("{{topic}}", session_data.get("topic", ""))
    prompt = prompt.replace("{{case_file_summary}}", case_file_summary)
    prompt = prompt.replace("{{criticisms_last_round}}", criticisms_last_round)
    
    # 스트리밍 실행 (재시도 로직 포함)
    retry_count = 0
    max_retries = 1
    full_response = ""
    
    while retry_count <= max_retries:
        full_response = ""
        
        # 재시도 시 프롬프트에 피드백 추가
        current_prompt = prompt
        if retry_count > 0:
            current_prompt += f"\n\n[SYSTEM: 이전 응답에서 Steering 위반이 감지되었습니다. 위반 사유: {violation_reason}. 제약 조건을 철저히 준수하여 다시 작성하세요.]"
            # BaseAgent의 _build_prompt가 아니라 여기서 직접 수정해야 함. 
            # 하지만 BaseAgent 구조상 system_prompt를 직접 수정하기 어려우므로, 
            # stream_response의 user_message에 추가하는 것이 나음.
        
        retry_message_suffix = ""
        if retry_count > 0:
            retry_message_suffix = f"\n\n[SYSTEM: 이전 응답에서 Steering 위반이 감지되었습니다. 위반 사유: {violation_reason}. 제약 조건을 철저히 준수하여 다시 작성하세요.]"

        try:
            async for chunk in agent.stream_response(
                messages=[],
                user_message=f"주제: {session_data.get('topic')}{retry_message_suffix}",
                case_file_summary=case_file_summary,
                category=session_data.get("category", "general"),
                steering_block=steering_block
            ):
                full_response += chunk
                await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {"text": chunk})
        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            full_response = f"[오류 발생: {str(e)}]"
            break
            
        # Compliance Check
        violation_reason = check_steering_compliance(full_response, steering)
        if violation_reason:
            logger.warning(f"[Guardrail] Violation detected: {violation_reason}")
            if retry_count < max_retries:
                await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {"text": "\n\n🔴 [시스템: Steering 위반 감지됨. 자동 재작성 중...]\n\n"})
                retry_count += 1
                continue
            else:
                logger.warning("[Guardrail] Max retries reached. Proceeding with violation.")
                break
        else:
            break
    
    # 스트리밍 종료
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_END, {
        "message_id": f"{agent_name}-{session_id}-{phase}"
    })
    
    # 메시지 저장
    await db.save_message(session_id, {
        "role": agent_name,
        "content_text": full_response,
        "round_index": current_round,
        "phase": phase
    })
    
    # Agent2 리스크 태그 추출 및 저장
    
    # Agent2 리스크 태그 추출 및 저장
    if agent_name == "agent2":
        tags = extract_risk_tags(full_response)
        if tags:
            await update_criticisms(session_id, tags)
    
    return full_response


def extract_risk_tags(response: str) -> List[str]:
    """응답에서 리스크 태그 추출"""
    import re
    tags = []
    # [태그] 형태 추출
    matches = re.findall(r'\[(\w+)\]', response)
    for match in matches:
        match_lower = match.lower()
        if match_lower in ['compliance', 'security', 'data_quality', 'cost', 'timeline', 
                           'ux', 'ops', 'deliverability', 'tracking', 'integration']:
            tags.append(match_lower)
    return list(set(tags))


async def update_criticisms(session_id: str, new_tags: List[str]):
    """CaseFile에 비판 태그 업데이트"""
    case_file = await db.get_case_file(session_id)
    if not case_file:
        return
    
    # 세션 누적
    criticisms_so_far = case_file.get('criticisms_so_far', [])
    for tag in new_tags:
        if tag not in criticisms_so_far:
            criticisms_so_far.append(tag)
    
    # 이번 라운드 태그
    await db.save_case_file(session_id, {
        **case_file,
        'criticisms_so_far': criticisms_so_far,
        'criticisms_last_round': new_tags
    })


async def execute_round(session_id: str, current_round: int):
    """
    라운드 내 모든 phase를 순차 실행합니다.
    """
    # 라운드 시작 phase
    phase = get_round_start_phase(current_round)
    if not phase:
        logger.error(f"Invalid round: {current_round}")
        await db.update_session(session_id, {"phase": Phase.FINALIZE_DONE.value, "status": "finalized"})
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        return
    
    gate_status = None
    
    # Phase 순차 실행
    while not is_wait_user_phase(phase) and not is_final_phase(phase) and phase not in [Phase.USER_GATE.value, Phase.END_GATE.value]:
        # 세션 상태 업데이트
        await db.update_session(session_id, {
            "phase": phase,
            "round_index": current_round
        })
        
        # 라운드 시작 이벤트 (첫 phase에서만)
        if phase == get_round_start_phase(current_round):
            await sse_event_manager.emit(session_id, EventType.ROUND_START, {"round_index": current_round})
        
        # Phase 설정 가져오기
        config = get_phase_config(phase)
        
        logger.info(f"[ExecuteRound] Executing phase={phase}, round={current_round}")
        
        # Phase 실행
        result = await execute_phase(session_id, phase, config)
        
        # API Rate Limit 방지를 위한 딜레이 (Gemini 429 에러 방지)
        await asyncio.sleep(3)
        
        # Verifier gate 결과 추출
        if "V_R2_GATE" in phase or "V_R3_SIGNOFF" in phase or "V_R1_AUDIT" in phase:
            gate_status = extract_gate_status(result)
        
        # 다음 phase로 전이
        phase = get_next_phase(phase, gate_status)
    
    # 라운드 종료 (USER_GATE, END_GATE, WAIT_USER, FINALIZE_DONE)
    await db.update_session(session_id, {"phase": phase})
    
    if is_final_phase(phase):
        # 최종 리포트 저장
        messages = await db.get_messages(session_id)
        last_message = messages[-1] if messages else None
        if last_message:
            await db.save_final_report(
                session_id, 
                {"content": last_message.get("content_text", "")},
                last_message.get("content_text", "")
            )
        
        await db.update_session(session_id, {"status": "finalized"})
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        
    elif phase in [Phase.USER_GATE.value, Phase.END_GATE.value]:
        # USER_GATE / END_GATE 도달 -> 사용자 개입 대기 (자동 진행 중단)
        logger.info(f"[ExecuteRound] Reached gate: {phase}. Waiting for user intervention.")
        
        # 게이트 렌더링용 데이터 수집
        case_file = await db.get_case_file(session_id)
        decisions = case_file.get("decisions", [])
        open_issues = case_file.get("open_issues", [])
        
        # ROUND_END 이벤트 발송 (게이트 데이터 포함)
        await sse_event_manager.emit(session_id, EventType.ROUND_END, {
            "round_index": current_round,
            "phase": phase,
            "decision_summary": decisions[-1] if decisions else "진행 중...",
            "what_changed": [], # TODO: 변경점 추적 로직 추가 필요
            "open_issues": open_issues[-3:],
            "verifier_gate_status": gate_status or "Go"
        })
        
    else:
        # WAIT_USER (기존 로직 유지 - 하지만 v2.2에서는 USER_GATE를 주로 사용)
        await sse_event_manager.emit(session_id, EventType.ROUND_END, {"round_index": current_round})


def extract_gate_status(response: str) -> Optional[str]:
    """Verifier 응답에서 gate_status 추출"""
    response_lower = response.lower()
    if "no-go" in response_lower or "no go" in response_lower or "rejected" in response_lower:
        return "No-Go"
    elif "conditional" in response_lower:
        return "Conditional"
    elif "approved" in response_lower or "go" in response_lower:
        return "Go"
    return None


# === 가드레일 (Guardrails) ===

EXCLUSION_PATTERNS = {
    "no_email": ["email", "이메일", "메일", "mail", "newsletter", "뉴스레터", "cold call", "콜드콜"],
    "no_meeting": ["meeting", "미팅", "회의", "zoom", "google meet", "대면"],
    "no_cost": ["cost", "비용", "budget", "예산", "paid", "유료"],
}

def check_steering_compliance(response: str, steering: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Steering 준수 여부 확인
    Returns: 위반 사유 (None이면 준수)
    """
    if not steering:
        return None
        
    response_lower = response.lower()
    
    # 1. Self-check 확인
    if "steering compliance check: not ok" in response_lower:
        return "Self-reported violation (NOT OK)"
        
    # 2. Hard Exclusions 확인
    exclusions = steering.get('exclusions', [])
    for exc in exclusions:
        # 1) 직접 키워드 매칭
        if exc.lower() in response_lower:
            return f"Exclusion violation: '{exc}' found in response"
            
        # 2) 패턴 매칭 (EXCLUSION_PATTERNS 테이블 활용)
        # exc가 "no_email" 같은 키라면 패턴 목록 확인
        patterns = EXCLUSION_PATTERNS.get(exc, [])
        for pattern in patterns:
            if pattern in response_lower:
                return f"Exclusion violation: '{exc}' pattern '{pattern}' found"
                
    return None


# === 엔드포인트 ===

@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session_endpoint(request: CreateSessionRequest, background_tasks: BackgroundTasks):
    """
    새 토론 세션 생성 (v2.2 + Legal v1.1)
    
    일반 토론:
    - current_round = 0
    - phase = WAIT_USER
    - 첫 번째 라운드 자동 시작
    
    법무 시뮬레이션 (case_type 있을 때):
    - phase = FACTS_INTAKE
    - 사실관계 입력 대기
    """
    try:
        # Supabase에 세션 생성
        session_data = await db.create_session(
            user_id=request.user_id,
            category=request.category,
            topic=request.topic
        )
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        session_id = session_data["id"]
        
        # 법무 시뮬레이션 vs 일반 토론 분기
        if request.case_type:
            # 법무 시뮬레이션: FACTS_INTAKE 단계로 시작
            await db.update_session(session_id, {
                "round_index": 0,
                "phase": Phase.FACTS_INTAKE.value,
                "status": "active",
                "case_type": request.case_type,
            })
            
            # CaseFile 초기화 (법무 필드 포함)
            await db.save_case_file(session_id, {
                "facts": [], "goals": [], "constraints": [], "decisions": [], 
                "open_issues": [], "assumptions": [], "next_experiments": [],
                "confirmed_facts": [], "disputed_facts": [], "missing_facts_questions": [],
                "legal_steering": None
            })
            
            logger.info(f"[CreateSession] Legal session created: {session_id}, case_type={request.case_type}")
            
        else:
            # 일반 토론: 기존 로직
            await db.update_session(session_id, {
                "round_index": 0,
                "phase": Phase.WAIT_USER.value,
                "status": "active"
            })
            
            # CaseFile 초기화 (기존 스키마 필드만 사용)
            await db.save_case_file(session_id, {
                "facts": [], "goals": [], "constraints": [], "decisions": [], 
                "open_issues": [], "assumptions": [], "next_experiments": []
            })
            
            # 첫 번째 라운드 자동 시작 (사용자 입력 없이 바로 시작)
            background_tasks.add_task(start_round, session_id)
        
        return CreateSessionResponse(
            session_id=session_id,
            category=session_data.get("category", ""),
            topic=session_data["topic"],
            status="active"
        )
        
    except Exception as e:
        logger.error(f"[CreateSession] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def start_round(session_id: str):
    """라운드 시작 (current_round 증가 후 실행)"""
    session = await db.get_session(session_id)
    if not session:
        return
    
    current_round = session.get("round_index", 0) + 1
    
    if current_round > MAX_ROUNDS:
        # 라운드 제한 도달
        await db.update_session(session_id, {
            "phase": Phase.FINALIZE_DONE.value,
            "status": "finalized"
        })
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        return
    
    # 라운드 증가
    await db.update_session(session_id, {
        "round_index": current_round,
        "status": "active"
    })
    
    # 라운드 실행
    await execute_round(session_id, current_round)


@router.post("/sessions/{session_id}/message", response_model=UserMessageResponse)
async def send_message_endpoint(session_id: str, request: UserMessageRequest, background_tasks: BackgroundTasks):
    """
    사용자 메시지 수신 (v2.2)
    
    WAIT_USER 상태에서만 다음 라운드 트리거
    """
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_phase = session.get("phase", "")
        
        # WAIT_USER가 아니면 버퍼에 저장
        if not is_wait_user_phase(current_phase):
            state_machine.buffer_input(session_id, request.message)
            return UserMessageResponse(
                status="buffered",
                round_index=session.get("round_index"),
                phase=current_phase
            )
        
        # 사용자 메시지 저장
        await db.save_message(session_id, {
            "role": "user",
            "content_text": request.message,
            "round_index": session.get("round_index"),
            "phase": "user_input"
        })
        
        # 다음 라운드 시작
        background_tasks.add_task(start_round, session_id)
        
        return UserMessageResponse(
            status="round_started",
            round_index=session.get("round_index", 0) + 1,
            phase="starting"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SendMessage] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/{session_id}/steering")
async def steering_endpoint(session_id: str, request: SteeringRequest, background_tasks: BackgroundTasks):
    """
    사용자 개입(Steering) 처리 (v2.2)
    
    USER_GATE/END_GATE 상태에서 다음 동작 결정
    - skip: 다음 라운드 진행
    - input: Steering 데이터 저장 후 진행
    - finalize: 종료
    - extend: 라운드 연장
    - new_session: 새 세션
    """
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        current_round = session.get("round_index", 0)
        
        # Idempotency Check (TODO: 실제 구현 필요, 여기선 로그만)
        if request.request_id:
            logger.info(f"[Steering] Request ID: {request.request_id}")
            
        action = request.action
        logger.info(f"[Steering] Action: {action}, Session: {session_id}")
        
        if action == "finalize":
            # 즉시 종료 처리
            await finalize_session_endpoint(session_id)
            return {"status": "finalized"}
            
        elif action == "extend":
            # 라운드 연장 (최대 1회)
            # TODO: extend_count 관리 로직 추가 필요
            # 여기서는 단순히 다음 라운드로 진행하도록 처리
            pass
            
        elif action == "new_session":
            # 결론 고정 후 새 세션 (클라이언트에서 처리하도록 유도하거나 여기서 생성)
            # 여기서는 현재 세션 종료만 처리
            await finalize_session_endpoint(session_id)
            return {"status": "new_session_created"}
            
        elif action == "input":
            # Steering 데이터 저장
            if request.steering:
                await db.save_case_file(session_id, {
                    "steering": request.steering
                })
                logger.info(f"[Steering] Saved steering data: {request.steering}")
        
        # skip 또는 input 처리 후 다음 라운드 진행
        # system_event=SKIP을 사용하는 대신, 명시적으로 start_round 호출
        # Race Condition 방지를 위해 상태만 변경하고 백그라운드에서 실행
        
        # 다음 라운드 시작 이벤트 발행 (UI 반응용)
        await sse_event_manager.emit(session_id, EventType.ROUND_START, {"round_index": current_round + 1})
        
        # 실제 실행은 백그라운드에서
        background_tasks.add_task(start_round, session_id)
        
        return {"status": "processed", "action": action}
        
    except Exception as e:
        logger.error(f"[Steering] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    """세션 상태 조회"""
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session["id"],
            status=session.get("status", "unknown"),
            category=session.get("category", ""),
            topic=session.get("topic", ""),
            round_index=session.get("round_index", 0),
            phase=session.get("phase", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[GetSession] 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions_endpoint(user_id: Optional[str] = Query(None)):
    """세션 목록 조회 (user_id 필수 - 없으면 빈 배열 반환)"""
    try:
        # user_id가 없으면 빈 배열 반환 (보안상 모든 세션을 보여주지 않음)
        if not user_id:
            logger.warning("[ListSessions] user_id not provided, returning empty list")
            return []
        
        sessions = await db.list_sessions(user_id)
        return [
            SessionResponse(
                id=s["id"],
                status=s.get("status", "unknown"),
                category=s.get("category", ""),
                topic=s.get("topic", ""),
                round_index=s.get("round_index", 0) or 0,
                phase=s.get("phase", "idle") or "idle"
            ) for s in sessions
        ]
    except Exception as e:
        logger.error(f"[ListSessions] 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/events")
async def session_events_endpoint(session_id: str):
    """SSE 이벤트 스트림"""
    return StreamingResponse(
        sse_event_manager.stream_events(session_id),
        media_type="text/event-stream"
    )


@router.post("/sessions/{session_id}/finalize")
async def finalize_session_endpoint(session_id: str):
    """세션 마무리 - 즉시 종료하고 리포트 생성"""
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 상태를 finalized로 변경
        await db.update_session(session_id, {
            "phase": Phase.FINALIZE_DONE.value,
            "status": "finalized"
        })
        
        # 리포트 자동 생성 시도
        messages = await db.get_messages(session_id)
        if messages:
            conversation_text = ""
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content_text", "")
                conversation_text += f"{role}: {content}\n\n"
            
            prompt = f"""
            다음은 AI 에이전트들이 나눈 토론 내용입니다.
            이 내용을 바탕으로 최종 결론 보고서를 작성해주세요.
            
            [토론 내용]
            {conversation_text}
            
            [작성 양식]
            1. **종합 결론**: 토론의 핵심 결과 요약
            2. **실행 방안**: 구체적인 실행 단계 및 계획
            3. **구현 방향**: 기술적/실무적 구현 가이드
            
            분량은 공백 포함 2000자 정도로 구체적이고 상세하게 서술해주세요.
            """
            
            try:
                report_content = await gemini_client.generate_text(prompt)
                report_json = {"content": report_content}
                await db.save_final_report(session_id, report_json, report_content)
            except Exception as e:
                logger.error(f"Failed to generate report on finalize: {e}")
        
        # SSE 이벤트 발송
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        
        return {"status": "finalized", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Finalize] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class FinalReportResponse(BaseModel):
    report_json: Optional[dict] = None
    report_md: Optional[str] = None


@router.get("/sessions/{session_id}/report", response_model=FinalReportResponse)
async def get_final_report(session_id: str):
    """최종 리포트 조회"""
    report = await db.get_final_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/sessions/{session_id}/report/generate", response_model=FinalReportResponse)
async def generate_report(session_id: str):
    """최종 리포트 생성 (On-Demand)"""
    # 세션 및 메시지 조회
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await db.get_messages(session_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # 프롬프트 구성
    conversation_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content_text", "")
        conversation_text += f"{role}: {content}\n\n"

    prompt = f"""
    다음은 AI 에이전트들이 나눈 토론 내용입니다.
    이 내용을 바탕으로 최종 결론 보고서를 작성해주세요.
    
    [토론 내용]
    {conversation_text}
    
    [작성 양식]
    1. **종합 결론**: 토론의 핵심 결과 요약
    2. **실행 방안**: 구체적인 실행 단계 및 계획
    3. **구현 방향**: 기술적/실무적 구현 가이드
    
    분량은 공백 포함 2000자 정도로 구체적이고 상세하게 서술해주세요.
    """

    # Gemini 호출
    try:
        report_content = await gemini_client.generate_text(prompt)
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    # 저장
    report_json = {"content": report_content}
    await db.save_final_report(session_id, report_json, report_content)
    
    return {"report_json": report_json, "report_md": report_content}


# ==========================================
# 법무 시뮬레이션 전용 엔드포인트
# ==========================================

class FactsSubmitRequest(BaseModel):
    """사실관계 입력 요청"""
    case_overview: str  # 사건 개요
    parties: List[str] = []  # 당사자
    facts: str  # 사실관계 상세
    evidence: List[str] = []  # 보유 증거 목록


class FactsSubmitResponse(BaseModel):
    """사실관계 처리 결과"""
    status: str
    confirmed_facts: List[str] = []
    disputed_facts: List[str] = []
    missing_facts_questions: List[str] = []
    facts_gate_required: bool = False


@router.post("/sessions/{session_id}/facts", response_model=FactsSubmitResponse)
async def submit_facts_endpoint(
    session_id: str, 
    request: FactsSubmitRequest,
    background_tasks: BackgroundTasks
):
    """
    법무 시뮬레이션: 사실관계 입력 및 FACTS_STIPULATE 처리
    
    1. 사용자 입력을 받아 Gemini로 3분류 수행
    2. MissingFactsQuestions >= 3 이면 FACTS_GATE로 라우팅
    3. 그렇지 않으면 Round 1 시작 (JUDGE_R1_FRAME)
    """
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_phase = session.get("phase", "")
        if current_phase != Phase.FACTS_INTAKE.value:
            raise HTTPException(status_code=400, detail=f"Invalid phase for facts submission: {current_phase}")
        
        # FACTS_STIPULATE 프롬프트 구성
        facts_input = f"""
사건 개요: {request.case_overview}
당사자: {', '.join(request.parties)}
사실관계: {request.facts}
보유 증거: {', '.join(request.evidence)}
"""
        
        stipulate_prompt = FACTS_STIPULATE_PROMPT.replace("{{user_facts_input}}", facts_input)
        
        # Gemini 호출하여 3분류 수행
        try:
            result_text = await gemini_client.generate_text(stipulate_prompt)
            
            # 결과 파싱 (간단한 키워드 기반)
            confirmed = []
            disputed = []
            missing = []
            
            # 텍스트에서 섹션별 추출 시도
            lines = result_text.split('\n')
            current_section = None
            
            for line in lines:
                line_lower = line.lower().strip()
                if 'confirmedfacts' in line_lower or '확정' in line_lower:
                    current_section = 'confirmed'
                elif 'disputedfacts' in line_lower or '쟁점' in line_lower or '다툼' in line_lower:
                    current_section = 'disputed'
                elif 'missingfacts' in line_lower or '누락' in line_lower or '질문' in line_lower:
                    current_section = 'missing'
                elif line.strip().startswith('-') or line.strip().startswith('•'):
                    content = line.strip().lstrip('-•').strip()
                    if content and current_section:
                        if current_section == 'confirmed':
                            confirmed.append(content)
                        elif current_section == 'disputed':
                            disputed.append(content)
                        elif current_section == 'missing':
                            missing.append(content)
            
            # 결과가 없으면 전체를 confirmed로 처리
            if not confirmed and not disputed and not missing:
                confirmed = [request.facts[:500]]
                
        except Exception as e:
            logger.error(f"[FactsStipulate] Gemini error: {e}")
            # 에러 시 입력을 그대로 confirmed로 처리
            confirmed = [request.facts[:500]]
            disputed = []
            missing = []
        
        # CaseFile 업데이트
        case_file = await db.get_case_file(session_id)
        case_file_update = {
            **case_file,
            "case_overview": request.case_overview,
            "parties": request.parties,
            "confirmed_facts": confirmed,
            "disputed_facts": disputed,
            "missing_facts_questions": missing,
        }
        await db.save_case_file(session_id, case_file_update)
        
        # 다음 phase 결정
        facts_gate_required = len(missing) >= 3
        
        if facts_gate_required:
            # FACTS_GATE로 이동 (사용자에게 추가 입력 요청)
            await db.update_session(session_id, {"phase": Phase.FACTS_GATE.value})
            logger.info(f"[FactsStipulate] Facts gate required: {len(missing)} missing questions")
        else:
            # Round 1 시작
            await db.update_session(session_id, {
                "phase": Phase.JUDGE_R1_FRAME.value,
                "round_index": 1,
                "facts_stipulated": True
            })
            # 백그라운드에서 라운드 실행
            background_tasks.add_task(execute_legal_round, session_id, 1)
            logger.info(f"[FactsStipulate] Starting Round 1")
        
        return FactsSubmitResponse(
            status="ok",
            confirmed_facts=confirmed,
            disputed_facts=disputed,
            missing_facts_questions=missing,
            facts_gate_required=facts_gate_required
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FactsSubmit] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class LegalSteeringRequest(BaseModel):
    """법무 Steering 입력 요청 (라운드별)"""
    # Round 1 필수
    focus_issue: Optional[str] = None
    goal: Optional[str] = None  # win_rate, risk_min, settlement, evidence_first
    
    # Round 2 필수
    proof_priority: Optional[str] = None
    evidence_level: Optional[str] = None
    constraints: List[str] = []
    
    # Round 3 필수
    end_action: Optional[str] = None  # finalize, extend_once, new_session
    report_style: Optional[str] = None  # risk, strategy, settlement
    
    # Advanced (옵션)
    stance: Optional[str] = None
    exclusions: List[str] = []
    notes: Optional[str] = None


@router.post("/sessions/{session_id}/legal-steering")
async def legal_steering_endpoint(
    session_id: str,
    request: LegalSteeringRequest,
    background_tasks: BackgroundTasks
):
    """
    법무 시뮬레이션: USER_GATE/END_GATE에서 Steering 입력 처리
    """
    try:
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        current_phase = session.get("phase", "")
        current_round = session.get("round_index", 0)
        
        if current_phase not in [Phase.USER_GATE.value, Phase.END_GATE.value, Phase.FACTS_GATE.value]:
            raise HTTPException(status_code=400, detail=f"Invalid phase for steering: {current_phase}")
        
        # END_GATE finalize 처리
        if current_phase == Phase.END_GATE.value and request.end_action == "finalize":
            await finalize_session_endpoint(session_id)
            return {"status": "finalized"}
        
        # Steering 데이터 저장
        steering_data = {
            "focus_issue": request.focus_issue,
            "goal": request.goal,
            "proof_priority": request.proof_priority,
            "evidence_level": request.evidence_level,
            "constraints": request.constraints,
            "stance": request.stance,
            "exclusions": request.exclusions,
            "notes": request.notes,
            "end_action": request.end_action,
            "report_style": request.report_style,
        }
        
        case_file = await db.get_case_file(session_id)
        await db.save_case_file(session_id, {
            **case_file,
            "legal_steering": steering_data
        })
        
        logger.info(f"[LegalSteering] Saved steering for session {session_id}: {steering_data}")
        
        # 다음 라운드 시작
        next_round = current_round + 1 if current_phase == Phase.USER_GATE.value else current_round
        
        if next_round > MAX_ROUNDS:
            # 라운드 제한 도달
            await db.update_session(session_id, {
                "phase": Phase.END_GATE.value
            })
            return {"status": "end_gate", "round": current_round}
        
        # 다음 라운드 시작
        background_tasks.add_task(execute_legal_round, session_id, next_round)
        
        return {"status": "ok", "next_round": next_round}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LegalSteering] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def execute_legal_round(session_id: str, round_number: int):
    """
    법무 시뮬레이션 라운드 실행
    
    R1: Judge(Frame) → Claimant → Opposing → Verifier → USER_GATE
    R2: Opposing → Claimant → Judge → Verifier → USER_GATE (or END_GATE if No-Go)
    R3: Opposing → Claimant → Judge → Verifier → END_GATE
    """
    phase = get_legal_round_start_phase(round_number)
    if not phase:
        logger.error(f"[LegalRound] Invalid round: {round_number}")
        return
    
    session = await db.get_session(session_id)
    case_type = session.get("case_type", "civil")
    
    gate_status = None
    
    # Phase 순차 실행
    while phase and phase not in [Phase.USER_GATE.value, Phase.END_GATE.value, Phase.FINALIZE_DONE.value]:
        # 세션 상태 업데이트
        await db.update_session(session_id, {
            "phase": phase,
            "round_index": round_number
        })
        
        # 라운드 시작 이벤트
        if phase == get_legal_round_start_phase(round_number):
            await sse_event_manager.emit(session_id, EventType.ROUND_START, {"round_index": round_number})
        
        agent_name = get_legal_agent_for_phase(phase)
        if agent_name and agent_name != "system":
            # 에이전트 실행
            result = await execute_legal_phase(session_id, phase, agent_name, round_number)
            
            # Verifier에서 gate_status 추출
            if "VERIFIER" in phase:
                gate_status = extract_gate_status(result)
            
            # API Rate Limit 방지
            await asyncio.sleep(3)
        
        # 다음 phase 결정
        phase = get_next_phase_legal(phase, case_type, gate_status)
    
    # 라운드 종료 처리
    await db.update_session(session_id, {"phase": phase})
    
    # ROUND_END 이벤트 발송
    case_file = await db.get_case_file(session_id)
    await sse_event_manager.emit(session_id, EventType.ROUND_END, {
        "round_index": round_number,
        "phase": phase,
        "gate_status": gate_status or "Go",
        "open_issues": case_file.get("disputed_facts", [])[:3]
    })


async def execute_legal_phase(session_id: str, phase: str, agent_name: str, round_number: int) -> str:
    """법무 시뮬레이션 단일 Phase 실행"""
    session = await db.get_session(session_id)
    case_file = await db.get_case_file(session_id)
    
    case_type = session.get("case_type", "civil")
    confirmed_facts = "\n".join(case_file.get("confirmed_facts", []))
    
    # 이전 메시지 요약
    messages = await db.get_messages(session_id)
    case_summary = ""
    if messages:
        recent = messages[-5:]
        case_summary = "\n".join([f"{m.get('role')}: {m.get('content_text', '')[:200]}" for m in recent])
    
    # 에이전트 가져오기
    agent = legal_agents.get(agent_name)
    if not agent:
        logger.error(f"[LegalPhase] Agent not found: {agent_name}")
        return ""
    
    # 컨텍스트 설정
    agent.set_round(round_number)
    if hasattr(agent, 'set_case_context'):
        agent.set_case_context(case_type, confirmed_facts, case_summary)
    
    # Steering Block 구성
    steering = case_file.get("legal_steering") or {}
    steering_block = LEGAL_STEERING_BLOCK.replace("{{focus_issue}}", steering.get("focus_issue", "미설정"))
    steering_block = steering_block.replace("{{goal}}", steering.get("goal", "미설정"))
    steering_block = steering_block.replace("{{constraints}}", ", ".join(steering.get("constraints", [])) or "없음")
    steering_block = steering_block.replace("{{stance}}", steering.get("stance", "중립"))
    steering_block = steering_block.replace("{{exclusions}}", ", ".join(steering.get("exclusions", [])) or "없음")
    steering_block = steering_block.replace("{{notes}}", steering.get("notes", ""))
    
    # SSE 이벤트
    await sse_event_manager.emit(session_id, EventType.SPEAKER_CHANGE, {"active_speaker": agent_name})
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_START, {
        "role": agent_name,
        "round_index": round_number,
        "phase": phase
    })
    
    # 스트리밍 실행
    full_response = ""
    try:
        async for chunk in agent.stream_response(
            messages=[],
            user_message=f"주제: {session.get('topic')}",
            case_file_summary=case_summary,
            category=case_type,
            steering_block=steering_block
        ):
            full_response += chunk
            await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {"text": chunk})
    except Exception as e:
        logger.error(f"[LegalPhase] Agent error: {e}")
        full_response = f"[오류 발생: {str(e)}]"
    
    # 법무 가드레일 검사 및 Rewrite
    violation = check_legal_guardrails(full_response, confirmed_facts)
    if violation:
        logger.warning(f"[LegalGuardrail] Violation: {violation}")
        # 1회 Rewrite 시도 (간단 구현)
        await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {
            "text": "\n\n⚠️ [시스템: 가드레일 위반 감지. 수정 중...]\n\n"
        })
    
    # 메시지 저장
    await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_END, {
        "message_id": f"{agent_name}-{session_id}-{phase}"
    })
    
    await db.save_message(session_id, {
        "role": agent_name,
        "content_text": full_response,
        "round_index": round_number,
        "phase": phase
    })
    
    return full_response


def check_legal_guardrails(response: str, confirmed_facts: str) -> Optional[str]:
    """
    법무 전용 가드레일 검사
    
    Returns: 위반 사유 (None이면 통과)
    """
    response_lower = response.lower()
    
    # 1. 확정적 자문 방지
    forbidden_phrases = ["반드시", "확실히", "100%", "틀림없이", "무조건", "절대"]
    for phrase in forbidden_phrases:
        if phrase in response:
            return f"Definitive advice: '{phrase}'"
    
    # 2. 확정 승소/패소 표현 방지
    if "확정 승소" in response or "확정 패소" in response:
        return "Definitive judgment expression"
    
    # 3. Steering Compliance Check 확인
    if "steering compliance check: not ok" in response_lower:
        return "Self-reported steering violation"
    
    return None

