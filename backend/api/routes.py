import asyncio
import logging
import uuid
import httpx
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from models.session import Session, SessionStatus, Category, Phase
from models.case_file import CaseFile
from orchestrator.state_machine import state_machine
from orchestrator.turn_manager import turn_manager, AgentRole, TurnType
from orchestrator.stop_detector import stop_detector, StopConfidence
from agents.base_agent import gemini_client
from agents.agent1_planner import Agent1Planner
from agents.agent2_critic import Agent2Critic
from agents.agent2_critic import Agent2Critic
from agents.agent3_synthesizer import Agent3Synthesizer
from agents.verifier import VerifierAgent
from storage import supabase_client as db
from .events import sse_event_manager, EventType
from config import BASE_URL  # config.py에 BASE_URL 추가 필요

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# 에이전트 인스턴스
agents = {
    AgentRole.AGENT1: Agent1Planner(gemini_client),
    AgentRole.AGENT2: Agent2Critic(gemini_client),
    AgentRole.AGENT3: Agent3Synthesizer(gemini_client),
    AgentRole.VERIFIER: VerifierAgent(gemini_client),
}


# Request/Response 모델
class CreateSessionRequest(BaseModel):
    category: str
    topic: str


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
    stop_confidence: Optional[str] = None
    trigger: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    status: str
    category: str
    topic: str
    round_index: int
    phase: str


# 비동기 턴 실행 함수 (Fire-and-Forget)
async def trigger_next_turn(session_id: str, turn_index: int):
    """
    다음 턴을 실행하기 위해 API를 비동기로 호출합니다.
    Vercel 타임아웃 방지를 위해 HTTP 요청을 보내고 응답을 기다리지 않거나,
    BackgroundTasks를 사용하지만, 여기서는 재귀적 호출 구조를 위해 API 호출을 사용합니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            # 로컬 테스트 시 BASE_URL이 필요함. 배포 시에는 배포 URL
            url = f"{BASE_URL}/api/sessions/{session_id}/next-turn"
            await client.post(url, json={"turn_index": turn_index}, timeout=1.0)
        except httpx.ReadTimeout:
            # 의도된 타임아웃 (Fire-and-Forget)
            pass
        except Exception as e:
            logger.error(f"[TriggerNextTurn] 호출 실패: {e}")


async def execute_turn(session_id: str, turn_index: int):
    """
    특정 턴을 실행하는 핵심 로직
    """
    turn_spec = turn_manager.get_turn(turn_index)
    if not turn_spec:
        logger.info(f"[ExecuteTurn] 모든 턴 완료. 세션 종료 처리.")
        await db.update_session(session_id, {"status": "finalized"})
        await sse_event_manager.emit(session_id, EventType.SESSION_END, {})
        return

    logger.info(f"[ExecuteTurn] 턴 시작 - index={turn_index}, role={turn_spec.role}, type={turn_spec.turn_type}")

    try:
        # 세션 및 CaseFile 조회
        session_data = await db.get_session(session_id)
        case_file_data = await db.get_case_file(session_id)
        
        # 이전 대화 맥락 구성 (최근 메시지 3개 정도만 요약 또는 전체 전달)
        # 여기서는 CaseFile Summary 대신 최근 메시지를 활용할 수도 있음
        # 하지만 현재 구조상 CaseFile Summary를 사용
        case_file_summary = ""
        if case_file_data:
            decisions = case_file_data.get('decisions', [])
            open_issues = case_file_data.get('open_issues', [])
            case_file_summary = f"결정사항: {'; '.join(decisions[-3:])}. 미해결: {'; '.join(open_issues[-3:])}"

        # 라운드 및 페이즈 업데이트
        current_round = turn_manager.get_round_index(turn_index)
        await db.update_session(session_id, {
            "round_index": current_round,
            "phase": f"{turn_spec.role}_{turn_spec.turn_type}"
        })

        # 이벤트 발송
        await sse_event_manager.emit(session_id, EventType.ROUND_START, {"round_index": current_round})
        await sse_event_manager.emit(session_id, EventType.SPEAKER_CHANGE, {"active_speaker": turn_spec.role})
        await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_START, {
            "role": turn_spec.role,
            "round_index": current_round,
            "phase": turn_spec.turn_type
        })

        # 에이전트 실행
        agent = agents[turn_spec.role]
        
        # 프롬프트 구성 (동적 지시사항 주입)
        system_prompt = agent.system_prompt.replace("{{turn_instruction}}", turn_spec.description)
        system_prompt = system_prompt.replace("{{max_chars}}", str(turn_spec.max_chars))
        system_prompt = system_prompt.replace("{{category}}", session_data.get("category", "general"))
        # 루브릭은 agent 내부에서 처리하거나 여기서 주입 (현재는 agent 코드에 {{rubric}} 플레이스홀더가 없으면 무시됨)
        
        # 스트리밍 실행
        full_response = ""
        async for chunk in agent.stream_response(
            messages=[], # 대화 히스토리는 문맥으로 전달됨
            user_message=f"주제: {session_data.get('topic')}", # 매 턴 주제 상기
            case_file_summary=case_file_summary,
            category=session_data.get("category", "general")
        ):
            full_response += chunk
            await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_CHUNK, {"text": chunk})

        # 스트리밍 종료 및 저장
        await sse_event_manager.emit(session_id, EventType.MESSAGE_STREAM_END, {
            "message_id": f"{turn_spec.role}-{session_id}-{turn_index}"
        })
        
        # 메시지 저장
        await db.save_message(session_id, {
            "role": turn_spec.role,
            "content_text": full_response,
            "round_index": current_round,
            "phase": turn_spec.turn_type,
            "event_id": turn_index
        })

        # 최종 리포트인 경우 별도 테이블에도 저장
        if turn_spec.turn_type == TurnType.FINAL_REPORT:
            logger.info(f"[ExecuteTurn] 최종 리포트 저장 중...")
            await db.save_final_report(session_id, {
                "report_json": {"content": full_response},
                "report_md": full_response
            })
            # 세션 상태 업데이트 (finalized)는 아래에서 처리됨

        # 다음 턴 트리거 (재귀 호출)
        next_turn_index = turn_index + 1
        if next_turn_index < turn_manager.get_total_turns():
            # 비동기로 다음 턴 호출 (Vercel 타임아웃 회피)
            await trigger_next_turn(session_id, next_turn_index)
        else:
            # 모든 턴 종료
            await db.update_session(session_id, {"status": "finalized"})
            await sse_event_manager.emit(session_id, EventType.SESSION_END, {})

    except Exception as e:
        logger.error(f"[ExecuteTurn] 오류 발생: {e}", exc_info=True)
        await sse_event_manager.emit(session_id, EventType.ERROR, {"error": str(e)})


class NextTurnRequest(BaseModel):
    turn_index: int

@router.post("/sessions/{session_id}/next-turn")
async def next_turn_endpoint(session_id: str, request: NextTurnRequest, background_tasks: BackgroundTasks):
    """
    다음 턴 실행을 위한 내부 엔드포인트
    """
    # 백그라운드 태스크로 실행하여 즉시 응답 반환
    background_tasks.add_task(execute_turn, session_id, request.turn_index)
    return {"status": "started", "turn_index": request.turn_index}


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session_endpoint(request: CreateSessionRequest, background_tasks: BackgroundTasks):
    """
    새 토론 세션 생성 및 첫 턴 시작
    """
    try:
        # Supabase에 세션 생성
        session_data = await db.create_session(
            user_id=None,
            category=request.category,
            topic=request.topic
        )
        
        if not session_data:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        session_id = session_data["id"]
        
        # CaseFile 초기화
        await db.save_case_file(session_id, {
            "facts": [], "goals": [], "constraints": [], "decisions": [], 
            "open_issues": [], "assumptions": [], "next_experiments": []
        })
        
        # 첫 번째 턴(Index 0) 시작
        background_tasks.add_task(execute_turn, session_id, 0)
        
        return CreateSessionResponse(
            session_id=session_id,
            category=session_data["category"],
            topic=session_data["topic"],
            status=session_data["status"]
        )
        
    except Exception as e:
        logger.error(f"[CreateSession] 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_endpoint(session_id: str):
    """
    세션 상태 조회
    """
    try:
        session_data = await db.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session_data["id"],
            status=session_data["status"],
            category=session_data["category"],
            topic=session_data["topic"],
            round_index=session_data.get("round_index", 0) or 0,
            phase=session_data.get("phase", "idle") or "idle"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions_endpoint(user_id: Optional[str] = Query(None)):
    """
    세션 목록 조회
    """
    try:
        # DB에서 세션 목록 조회 (supabase_client에 list_sessions 추가 필요)
        sessions = await db.list_sessions(user_id)
        return [
            SessionResponse(
                id=s["id"],
                status=s["status"],
                category=s["category"],
                topic=s["topic"],
                round_index=s.get("round_index", 0) or 0,
                phase=s.get("phase", "idle") or "idle"
            ) for s in sessions
        ]
    except Exception as e:
        logger.error(f"[ListSessions] 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FinalReportResponse(BaseModel):
    report_json: dict
    report_md: str


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
    # 1. 세션 및 메시지 조회
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await db.get_messages(session_id)
    if not messages:
        raise HTTPException(status_code=400, detail="No messages to summarize")

    # 2. 프롬프트 구성
    conversation_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content_text", "")
        conversation_text += f"{role}: {content}\n\n"

    prompt = f"""
    다음은 3명의 AI 에이전트(Agent 1: 계획, Agent 2: 비판, Agent 3: 종합)가 나눈 토론 내용입니다.
    이 내용을 바탕으로 최종 결론 보고서를 작성해주세요.
    
    [토론 내용]
    {conversation_text}
    
    [작성 양식]
    1. **종합 결론**: 토론의 핵심 결과 요약
    2. **실행 방안**: 구체적인 실행 단계 및 계획
    3. **구현 방향**: 기술적/실무적 구현 가이드
    
    분량은 공백 포함 1500자 내외로 상세하게 작성해주세요.
    """

    # 3. Gemini 호출
    try:
        response = await gemini_client.generate_content(prompt)
        report_content = response.text
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    # 4. 저장
    report_data = {
        "report_json": {"content": report_content},
        "report_md": report_content
    }
    await db.save_final_report(session_id, report_data)
    
    return report_data



# 기존 메시지 전송, 종료, 리포트 엔드포인트는 유지하되 필요 시 수정
# 현재 대화형 모드에서는 사용자 개입이 최소화되므로 send_message 등의 중요도가 낮아짐
