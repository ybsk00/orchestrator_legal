"""
Supabase 클라이언트 (백엔드용)

Service Role Key를 사용하여 RLS를 우회하고 관리자 작업 수행
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

_client: Client = None


def get_supabase_client() -> Client:
    """Supabase 클라이언트 싱글톤"""
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase credentials not configured")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


# 헬퍼 함수들
async def create_session(user_id: str, category: str, topic: str) -> dict:
    """새 세션 생성"""
    client = get_supabase_client()
    result = client.table("sessions").insert({
        "user_id": user_id,
        "category": category,
        "topic": topic,
    }).execute()
    return result.data[0] if result.data else None


async def get_session(session_id: str) -> dict:
    """세션 조회"""
    client = get_supabase_client()
    result = client.table("sessions").select("*").eq("id", session_id).single().execute()
    return result.data


async def list_sessions(user_id: str = None) -> list:
    """세션 목록 조회"""
    client = get_supabase_client()
    query = client.table("sessions").select("*").order("created_at", desc=True)
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.execute()
    return result.data or []


async def update_session(session_id: str, updates: dict) -> dict:
    """세션 업데이트"""
    client = get_supabase_client()
    result = client.table("sessions").update(updates).eq("id", session_id).execute()
    return result.data[0] if result.data else None


async def save_message(session_id: str, message_data: dict) -> dict:
    """메시지 저장"""
    client = get_supabase_client()
    message_data["session_id"] = session_id
    result = client.table("messages").insert(message_data).execute()
    return result.data[0] if result.data else None


async def get_messages(session_id: str) -> list:
    """세션 메시지 조회"""
    client = get_supabase_client()
    result = client.table("messages").select("*").eq("session_id", session_id).order("created_at").execute()
    return result.data or []


async def save_case_file(session_id: str, case_file_data: dict) -> dict:
    """CaseFile 저장/업데이트"""
    client = get_supabase_client()
    case_file_data["session_id"] = session_id
    result = client.table("case_files").upsert(case_file_data).execute()
    return result.data[0] if result.data else None


async def get_case_file(session_id: str) -> dict:
    """CaseFile 조회"""
    client = get_supabase_client()
    result = client.table("case_files").select("*").eq("session_id", session_id).single().execute()
    return result.data


async def save_final_report(session_id: str, report_json: dict, report_md: str = None) -> dict:
    """최종 리포트 저장"""
    client = get_supabase_client()
    result = client.table("final_reports").insert({
        "session_id": session_id,
        "report_json": report_json,
        "report_md": report_md,
    }).execute()
    return result.data[0] if result.data else None


async def get_final_report(session_id: str) -> dict:
    """최종 리포트 조회"""
    client = get_supabase_client()
    result = client.table("final_reports").select("*").eq("session_id", session_id).single().execute()
    return result.data
